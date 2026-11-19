"""The generic reader (T-0030, ADR 0003): its two seams, `read(language, file, source)` and `contribute(project)`."""

from __future__ import annotations

import textwrap
from pathlib import Path

import graphe_generic
from graphe_generic import GO, JAVA, RUST


def _read(language, file: str, source: str):
    """The definitions (kind, name, line) and the uses (kind, name, line, owner's name) an agent would see."""
    definitions, uses = graphe_generic.read(language, file, textwrap.dedent(source).encode())
    return ({(d.kind, d.name, d.line) for d in definitions},
            {(u.kind, u.name, u.line, u.owner.name if u.owner else None) for u in uses})


def test_a_go_method_declared_outside_its_type_is_type_dot_method():
    definitions, uses = _read(GO, "a/t.go", """\
        package a

        type T struct {
        \tBase
        }

        func (r *T) M() {
        \tf()
        \tr.N()
        \t_ = &T{}
        }

        func (r T[K]) N() {}

        func (r *U[K]) O() {}

        func f() {
        \tfmt.Println(1)
        \tg[int](1)
        \th[int, string](1, 2)
        }
        """)
    assert definitions == {("class", "T", 3), ("method", "T.M", 7), ("method", "T.N", 13), ("method", "U.O", 15),
                           ("function", "f", 17)}
    assert uses == {("reference", "Base", 4, "T"), ("call", "f", 8, "T.M"), ("send", "N", 9, "T.M"),
                    ("reference", "T", 10, "T.M"), ("send", "Println", 18, "f"),
                    ("call", "g", 19, "f"), ("call", "h", 20, "f")}


def test_a_rust_function_of_an_impl_is_a_method_of_its_type():
    definitions, uses = _read(RUST, "src/t.rs", """\
        struct T;

        impl<K> Display for T<K> {
            fn f(&self) {
                g();
                self.h();
                T::new();
                let _ = T {};
            }
        }

        trait Shape {
            fn area(&self) -> f64 { 0.0 }
            fn sides(&self);
        }

        fn g() {
            println!("x");
        }

        impl<'a> From<&'a U> for &'a mut U {
            fn from(u: &'a U) -> Self { u }
        }
        """)
    assert definitions == {("class", "T", 1), ("method", "T.f", 4), ("class", "Shape", 12),
                           ("method", "Shape.area", 13), ("function", "g", 17), ("class", "U", 21),
                           ("method", "U.from", 22)}
    assert uses == {("call", "g", 5, "T.f"), ("send", "h", 6, "T.f"), ("send", "new", 7, "T.f"),
                    ("reference", "T", 8, "T.f")}


def test_a_java_class_its_methods_and_what_it_builds():
    definitions, uses = _read(JAVA, "src/C.java", """\
        class C extends B implements I {
            C() {
                init();
            }

            void m() {
                list.add(new D());
                this.n();
            }
        }

        interface I {
            void abstractOne();
            default void n() {}
        }
        """)
    assert definitions == {("class", "C", 1), ("method", "C.C", 2), ("method", "C.m", 6), ("class", "I", 12),
                           ("method", "I.n", 14)}
    assert uses == {("reference", "B", 1, "C"), ("reference", "I", 1, "C"), ("call", "init", 3, "C.C"),
                    ("send", "add", 7, "C.m"), ("reference", "D", 7, "C.m"), ("send", "n", 8, "C.m")}


class Project:
    """What `contribute(project)` receives (docs/contribution.md), over files in a temporary folder."""

    def __init__(self, root: Path, files: dict[str, str]) -> None:
        self.root, self.configuration, self.graph, self.checking = root, {}, {"nodes": {}, "links": []}, False
        for rel, text in files.items():
            (root / rel).parent.mkdir(parents=True, exist_ok=True)
            (root / rel).write_text(textwrap.dedent(text), encoding="utf-8")

    def files(self, suffix: str) -> list[Path]:
        return sorted(p for p in self.root.rglob(f"*{suffix}") if p.name.endswith(suffix))


def test_a_call_is_linked_by_its_name_only_when_the_language_defines_it_once(tmp_path: Path, capsys):
    project = Project(tmp_path, {
        "a/a.go": """\
            package a

            func Unique() {}

            func (s *Store) Save() {}

            func (s *Store) Get() {}

            func caller(x *Store) {
            \tUnique()
            \tx.Save()
            \tx.Get()
            \tb.Twice()
            \tShared()
            \tfmt.Println()
            }
            """,
        "b/b.go": """\
            package b

            func Twice() {}

            type Store struct{}
            """,
        "c/c.go": """\
            package c

            func Twice() {}
            """,
        "lib/shared.rs": "fn Shared() {}\nfn helper() { Unique(); }\n",
        "broken/x.go": "package x\n\nfunc (( {\n",
    })
    # a host without Java: no contribution at all, no coverage (T-0031)
    assert graphe_generic.contribute(JAVA, project) == {}

    go = graphe_generic.contribute(GO._replace(common=frozenset({"Get"})), project)
    nodes = {n["id"]: (n["kind"], n["name"], n["source_location"]) for n in go["nodes"]}
    assert nodes["a_a_go"] == ("file", "a/a.go", "L1")
    assert nodes["a_a_go_store_save"] == ("method", "Store.Save", "L5")
    assert "broken_x_go" not in nodes
    assert "broken/x.go" in capsys.readouterr().err
    calls = {(e["source"], e["target"], e["confidence"]) for e in go["links"] if e["relation"] == "calls"}
    assert calls == {("a_a_go_caller", "a_a_go_unique", "INFERRED"), ("a_a_go_caller", "a_a_go_store_save", "INFERRED")}
    contains = {(e["source"], e["target"]) for e in go["links"] if e["relation"] == "contains"}
    assert ("b_b_go", "b_b_go_store") in contains and ("a_a_go", "a_a_go_store_save") in contains
    verdicts = {s["text"]: s["verdict"] for s in go["sites"]}
    assert verdicts == {"Unique": "ours?", "x.Save": "ours?", "x.Get": "common", "b.Twice": "ambiguous",
                        "Shared": "external", "fmt.Println": "external"}
    rust = graphe_generic.contribute(RUST, project)
    assert not [e for e in rust["links"] if e["relation"] == "calls"]
    assert {s["text"]: s["verdict"] for s in rust["sites"]} == {"Unique": "external"}
