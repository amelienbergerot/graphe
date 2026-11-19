"""The generic reader (T-0030, ADR 0003): its two seams, `read(language, file, source)` and `contribute(project)`."""

from __future__ import annotations

import textwrap
from pathlib import Path

import networkx as nx

import graphe
import graphe_generic
from graphe_generic import C, CSHARP, GO, JAVA, JVM, KOTLIN, PHP, RUBY, RUST, SWIFT


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


def test_a_go_file_in_go_1_26s_syntax_is_read_for_its_valid_part():
    """gitea (T-0039): the grammar knows neither a generic method nor `new(expr)`; the file is read all the same. The
    generic method is lost in the error: its call belongs to the file."""
    definitions, uses = _read(GO, "a/flash.go", """\
        package a

        type Flash struct{}

        func (f *Flash) Error[T any](msg T) {
        \tf.set(msg)
        }

        func before() {
        \tp := new(int64(1))
        \tg()
        }

        func after() {
        \th()
        }
        """)
    assert definitions == {("class", "Flash", 3), ("function", "before", 9), ("function", "after", 14)}
    assert uses == {("send", "set", 6, None), ("call", "new", 10, "before"), ("call", "g", 11, "before"),
                    ("call", "h", 15, "after")}


def test_a_rust_file_with_a_lifetime_first_in_a_trait_object_is_read_for_its_valid_part():
    """libsignal (T-0040): grammar 0.24.2 rejects `dyn 's + Trait`; the file is read all the same, even the method
    whose signature holds the error."""
    definitions, uses = _read(RUST, "src/tokio.rs", """\
        struct Context;

        impl Context {
            fn run_boxed<'s>(&'s self, make: Box<dyn 's + FnOnce() -> u8>) -> u8 {
                prepare();
                make()
            }

            fn spawn_it(&self) {
                self.run_boxed(Box::new(|| 1));
            }
        }

        fn after() {
            helper();
        }
        """)
    assert definitions == {("class", "Context", 1), ("method", "Context.run_boxed", 4),
                           ("method", "Context.spawn_it", 9), ("function", "after", 14)}
    assert uses == {("call", "prepare", 5, "Context.run_boxed"), ("call", "make", 6, "Context.run_boxed"),
                    ("send", "run_boxed", 10, "Context.spawn_it"), ("send", "new", 10, "Context.spawn_it"),
                    ("call", "helper", 15, "after")}


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



def test_rust_functions_of_one_name_in_a_file_are_one():
    """libsignal (T-0033): `impl Debug for T` and `impl Display for T` both define `fmt`, one `T.fmt`; the `fn f` of two
    `mod`s of one file, one `f`."""
    definitions, _ = _read(RUST, "src/t.rs", """        impl Debug for T {
            fn fmt(&self) {}
        }
        impl Display for T {
            fn fmt(&self) {}
        }
        mod a { fn f() {} }
        mod b { fn f() {} }
        """)
    assert definitions == {("class", "T", 1), ("method", "T.fmt", 2), ("function", "f", 7)}
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


def test_java_overloads_are_one_method_and_a_scoped_type_is_its_last_name():
    """protobuf (T-0033): `o(int)` and `o(String)` are one `A.o`, else every call to it is ambiguous; generated code
    builds and extends `Outer.Inner` and `com.x.D`."""
    definitions, uses = _read(JAVA, "src/A.java", """        class A extends GeneratedMessage.Builder<A> {
            void o(int i) {
                new com.x.D();
            }

            void o(String s) {
                o(1);
                new Outer.Inner<A>();
            }
        }

        interface AOrBuilder extends I, com.google.protobuf.MessageOrBuilder {}
        """)
    assert definitions == {("class", "A", 1), ("method", "A.o", 2), ("class", "AOrBuilder", 12)}
    assert uses == {("reference", "Builder", 1, "A"), ("reference", "D", 3, "A.o"), ("call", "o", 7, "A.o"),
                    ("reference", "Inner", 8, "A.o"), ("reference", "I", 12, "AOrBuilder"),
                    ("reference", "MessageOrBuilder", 12, "AOrBuilder")}


def test_a_java_nested_class_is_outer_dot_inner_and_an_anonymous_ones_methods_are_its_enclosing_classs():
    """protobuf (T-0043): each generated message's `Builder` is `Message.Builder`, else the `Builder`s of one file are
    one class; an anonymous class is still no class (a `shortcut:`)."""
    definitions, uses = _read(JAVA, "src/Outer.java", """        class Outer {
            void m() { new Inner(); new Runnable() { public void run() { go(); } }; }

            static class Inner {
                void m() { helper(); }

                class Deeper {
                    Deeper() {}
                }
            }
        }

        class Top {}
        """)
    assert definitions == {("class", "Outer", 1), ("method", "Outer.m", 2), ("method", "Outer.run", 2),
                           ("class", "Outer.Inner", 4), ("method", "Outer.Inner.m", 5),
                           ("class", "Outer.Inner.Deeper", 7), ("method", "Outer.Inner.Deeper.Deeper", 8),
                           ("class", "Top", 13)}
    assert uses == {("reference", "Inner", 2, "Outer.m"), ("reference", "Runnable", 2, "Outer.m"),
                    ("call", "go", 2, "Outer.run"), ("call", "helper", 5, "Outer.Inner.m")}


def test_a_cpp_method_defined_outside_its_class_is_named_by_its_innermost_scope():
    """protobuf (T-0034): `ns::Foo::Bar`, `Foo<T>::Bar`, a constructor, a destructor, an operator; a prototype and a
    method declared in its class are not definitions; a file with a macro the grammar does not know is read; an
    anonymous `enum : int` is no class; the macros of `class PROTOBUF_EXPORT Foo` and
    `Get() const ABSL_ATTRIBUTE_LIFETIME_BOUND {` are erased: the grammar would read a function `Foo`, and no `Get`."""
    definitions, uses = _read(C, "src/foo.cc", """        namespace ns {
        class PROTOBUF_EXPORT PROTOBUF_DECLSPEC_EMPTY_BASES Foo : public Base, public ns::Mixin<int> {
          int declared();
          int inline_one() { return helper<int>(); }
          Foo(const Foo&) = default;
        };
        }
        int prototype(int);
        void ns::Foo::Bar() { p->m(); std::move(x); a::b::c(); }
        template <typename T> const T& Foo<T>::Get() const { return new ns::Thing<T>(); }
        Foo::Foo() : x(1) { init(); }
        Foo::~Foo() {}
        bool Foo::operator==(const Foo& o) const { return true; }
        static char** names(void) { return 0; }
        PROTOBUF_EXPORT void exported() { f(); }
        class Bits { enum : int { kA = 1 }; };
        struct URL final { void Parse() {} };
        const T& Holder::Get() const ABSL_ATTRIBUTE_LIFETIME_BOUND { return v(); }
        """)
    assert definitions == {("class", "Foo", 2), ("method", "Foo.inline_one", 4), ("method", "Foo.Bar", 9),
                           ("method", "Foo.Get", 10), ("method", "Foo.Foo", 11), ("method", "Foo.~Foo", 12),
                           ("method", "Foo.operator==", 13), ("function", "names", 14),
                           ("function", "exported", 15), ("class", "Bits", 16),
                           ("class", "URL", 17), ("method", "URL.Parse", 17),
                           ("method", "Holder.Get", 18)}
    assert uses == {("reference", "Base", 2, "Foo"), ("reference", "Mixin", 2, "Foo"),
                    ("call", "helper", 4, "Foo.inline_one"), ("send", "m", 9, "Foo.Bar"),
                    ("send", "move", 9, "Foo.Bar"), ("send", "c", 9, "Foo.Bar"), ("reference", "Thing", 10, "Foo.Get"),
                    ("call", "init", 11, "Foo.Foo"), ("call", "f", 15, "exported"),
                    ("call", "v", 18, "Holder.Get")}


def test_a_c_function_its_structs_and_a_forward_declaration_that_is_none():
    """upb (T-0034): `UPB_INLINE` erased, a `typedef struct {..} T` is a class `T`, `struct upb_Arena;` no class."""
    definitions, uses = _read(C, "upb/a.c", """        typedef struct { int a; } Anon;
        struct upb_Arena { int b; };
        struct upb_Arena;
        UPB_INLINE void* upb_Arena_Malloc(upb_Arena* a) { return a->alloc(_upb_size(a)); }
        """)
    assert definitions == {("class", "Anon", 1), ("class", "upb_Arena", 2), ("function", "upb_Arena_Malloc", 4)}
    assert uses == {("send", "alloc", 4, "upb_Arena_Malloc"), ("call", "_upb_size", 4, "upb_Arena_Malloc")}


def test_a_csharp_class_its_members_and_both_kinds_of_call():
    """protobuf (T-0035): the upstream `tags.scm` captures only `x.M()`; a bare `F()` is ours too. A base given by
    the `pb::` alias of generated code, a generic or a qualified name is a reference by its last name, as what `new`
    builds; an abstract or interface method without a body is no definition, as Java's; a constructor is `C.C`."""
    definitions, uses = _read(CSHARP, "src/C.cs", """        namespace N.M {
        sealed partial class C : pb::IMessage<C>, global::System.IEquatable<C>, B {
            C() { Init(); }
            void M() { list.Add(new D()); this.N(); x?.O(); F<int>(1); }
            int L() => new pb::E<int>().P();
            abstract void A();
        }
        interface I { void X(); void Y() {} }
        struct S {}
        enum K {}
        record R(int A) : Q(A);
        }
        """)
    assert definitions == {("class", "C", 2), ("method", "C.C", 3), ("method", "C.M", 4), ("method", "C.L", 5),
                           ("class", "I", 8), ("method", "I.Y", 8), ("class", "S", 9), ("class", "K", 10),
                           ("class", "R", 11)}
    assert uses == {("reference", "IMessage", 2, "C"), ("reference", "IEquatable", 2, "C"), ("reference", "B", 2, "C"),
                    ("call", "Init", 3, "C.C"), ("send", "Add", 4, "C.M"), ("reference", "D", 4, "C.M"),
                    ("send", "N", 4, "C.M"), ("send", "O", 4, "C.M"), ("call", "F", 4, "C.M"),
                    ("reference", "E", 5, "C.L"), ("send", "P", 5, "C.L"),
                    ("reference", "Q", 11, "R")}


def test_a_csharp_nested_class_is_outer_dot_inner():
    """protobuf (T-0043): each generated message's `Types` is `Message.Types`, else the `Types` of one file are one."""
    definitions, uses = _read(CSHARP, "src/Person.cs", """        namespace N {
        public sealed partial class Person {
            public static partial class Types {
                public enum PhoneType { Mobile }
                public sealed partial class PhoneNumber {
                    public void M() { F(); }
                }
            }
        }
        }
        """)
    assert definitions == {("class", "Person", 2), ("class", "Person.Types", 3), ("class", "Person.Types.PhoneType", 4),
                           ("class", "Person.Types.PhoneNumber", 5), ("method", "Person.Types.PhoneNumber.M", 6)}
    assert uses == {("call", "F", 6, "Person.Types.PhoneNumber.M")}


def test_a_csharp_property_is_the_method_c_dot_p_owning_its_accessors_calls():
    """protobuf (T-0041): a generated setter's `CheckNotNull` is `Person.Name`'s, not `Person`'s; `=> expr` and
    `get => expr` too. An auto-property is a node with no call; its initial value's call is its own. An interface's or
    abstract property has no body, as a signature: no node."""
    definitions, uses = _read(CSHARP, "src/Person.cs", """        class Person {
            string name_;
            public string Name {
                get { return name_; }
                set { name_ = ProtoPreconditions.CheckNotNull(value, "value"); }
            }
            int Size => Compute();
            int Id { get => Read(); }
            int Age { get; set; }
            int Tag { get; } = Init();
        }
        interface IPerson { string Name { get; } }
        abstract class Base { public abstract string Name { get; } }
        """)
    assert definitions == {("class", "Person", 1), ("method", "Person.Name", 3), ("method", "Person.Size", 7),
                           ("method", "Person.Id", 8), ("method", "Person.Age", 9), ("method", "Person.Tag", 10),
                           ("class", "IPerson", 12), ("class", "Base", 13)}
    assert uses == {("send", "CheckNotNull", 5, "Person.Name"), ("call", "Compute", 7, "Person.Size"),
                    ("call", "Read", 8, "Person.Id"), ("call", "Init", 10, "Person.Tag")}


def test_a_csharp_preprocessor_directive_cutting_a_base_list_or_an_expression_costs_nothing():
    """protobuf (T-0035): generated code cuts its base list with `#if`, which the grammar does not parse (44 of its
    224 files skipped, 42 of them for that): the directives are erased, both branches read; one expression whose two branches then follow
    each other (`= new[] {1}; new[] {2};`) leaves an error, read all the same."""
    definitions, uses = _read(CSHARP, "src/Person.pb.cs", """        public sealed partial class Person : pb::IMessage<Person>
          #if !GOOGLE_PROTOBUF_REFSTRUCT_COMPATIBILITY_MODE
            , pb::IBufferMessage
          #endif
        {
            void M() {
                var e =
        #if NET5_0_OR_GREATER
                    new[] { 1 };
        #else
                    new[] { 2 };
        #endif
                Check(e);
            }
        }
        """)
    assert definitions == {("class", "Person", 1), ("method", "Person.M", 6)}
    assert uses == {("reference", "IMessage", 1, "Person"), ("reference", "IBufferMessage", 3, "Person"),
                    ("call", "Check", 13, "Person.M")}


def test_a_ruby_class_its_methods_and_its_explicit_calls():
    """protobuf (T-0036): a module is a class, a `class << self` none, `X.class_eval do` reopens `X`
    (well_known_types.rb's `Any.pack`); `b()`, `c arg`, `x.c`, `self.f` are calls; `C.new` and a superclass are
    references by the last name."""
    definitions, uses = _read(RUBY, "lib/c.rb", """\
        module Google::Protobuf
          class C < Google::Protobuf::B
            def initialize(a); b(); d 1; x.c; self.f; Foo::Bar.new(1); end
            def self.s; end
            def x=(v); end
            class << self
              def t; y&.z; end
            end
          end
          Any.class_eval do
            def pack; end
          end
          def self.encode(m); end
        end
        def top; end
        """)
    # a class in a module is `Module.Class` (T-0043), the module by its last name
    assert definitions == {("class", "Protobuf", 1), ("class", "Protobuf.C", 2), ("method", "Protobuf.C.initialize", 3),
                           ("method", "Protobuf.C.s", 4), ("method", "Protobuf.C.x=", 5), ("method", "Protobuf.C.t", 7),
                           ("class", "Protobuf.Any", 10), ("method", "Protobuf.Any.pack", 11),
                           ("method", "Protobuf.encode", 13), ("function", "top", 15)}
    init = "Protobuf.C.initialize"
    assert uses == {("reference", "B", 2, "Protobuf.C"), ("call", "b", 3, init), ("call", "d", 3, init),
                    ("send", "c", 3, init), ("send", "f", 3, init), ("send", "new", 3, init),
                    ("reference", "Bar", 3, init), ("send", "z", 7, "Protobuf.C.t"),
                    ("send", "class_eval", 10, "Protobuf.Any")}


def test_a_ruby_local_variable_is_no_call():
    """T-0036: the upstream `tags.scm` takes a bare identifier for a call; it may be a variable. A bare method call
    `e` is missed too (docs/readers.md)."""
    _, uses = _read(RUBY, "lib/v.rb", """\
        def m
          v = 1
          v
          e
          v.succ
        end
        """)
    assert uses == {("send", "succ", 5, "m")}


def test_a_php_function_its_classes_methods_and_top_level_calls():
    """4cast (T-0044): a top-level call is its file's (as the PHP reader's since T-0023), a method is `Class.method`, an
    interface's signature is none, the HTML outside `<?php ?>` holds no call; `x->m()`, `x?->m()`, `X::m()` are sends,
    `new C`, `extends`, `implements` and a trait's `use` references by the last name."""
    definitions, uses = _read(PHP, "api/index.php", """\
        <?php
        $db = ouvrir();
        \\A\\route_zones($db);
        function route_zones($db) { return array_map(fn($z) => $z->nom(), (new \\A\\Zone())->all()); }
        class Zone extends Base implements I { use T;
          public function __construct() { parent::__construct(); self::make(); $this?->go(); $f(); }
        }
        interface I { function f(); }
        ?>
        <p>aide(x)</p>
        """)
    assert definitions == {("function", "route_zones", 4), ("class", "Zone", 5), ("method", "Zone.__construct", 6),
                           ("class", "I", 8)}
    init = "Zone.__construct"
    assert uses == {("call", "ouvrir", 2, None), ("call", "route_zones", 3, None),
                    ("call", "array_map", 4, "route_zones"), ("send", "nom", 4, "route_zones"),
                    ("reference", "Zone", 4, "route_zones"), ("send", "all", 4, "route_zones"),
                    ("reference", "Base", 5, "Zone"), ("reference", "I", 5, "Zone"), ("reference", "T", 5, "Zone"),
                    ("send", "__construct", 6, init), ("send", "make", 6, init), ("send", "go", 6, init)}


def test_a_swift_type_its_methods_and_its_calls():
    """libsignal (T-0037): a class, a struct, an enum, an actor and a protocol are classes; `init` is the method
    `C.init`, a computed property `p` the method `C.p`; `b()` is a call, `x.c()`, `y?.z()` and `.make()` are sends; a call to a capitalised name, `C(..)`,
    `Foo.Bar(..)`, `Foo.Array<Int>()`, and an inherited type, generic too, are references by the last name."""
    definitions, uses = _read(SWIFT, "Sources/c.swift", """\
        import Foundation
        public class C: B, P {
            init(a: Int) { b(); x.c(); self.f(1); y?.z(); Foo.Bar(x: 1) }
            func m() -> Int { return .make() }
            static func s() { C.s() }
            var p: Int { g() }
        }
        struct S: Base<T> { func t() { let q = C(a: 1); q.m(); Foo.Array<Int>() } }
        protocol P { func v() }
        func top() { [1].map { $0.u() } }
        """)
    assert definitions == {("class", "C", 2), ("method", "C.init", 3), ("method", "C.m", 4), ("method", "C.s", 5),
                           ("method", "C.p", 6), ("class", "S", 8), ("method", "S.t", 8), ("class", "P", 9), ("function", "top", 10)}
    assert uses == {("reference", "B", 2, "C"), ("reference", "P", 2, "C"), ("call", "b", 3, "C.init"),
                    ("send", "c", 3, "C.init"), ("send", "f", 3, "C.init"), ("send", "z", 3, "C.init"),
                    ("reference", "Bar", 3, "C.init"), ("send", "make", 4, "C.m"), ("send", "s", 5, "C.s"),
                    ("call", "g", 6, "C.p"), ("reference", "C", 8, "S.t"), ("send", "m", 8, "S.t"),
                    ("reference", "Base", 8, "S"), ("reference", "Array", 8, "S.t"), ("send", "map", 10, "top"), ("send", "u", 10, "top")}


def test_a_swift_extension_is_no_class_its_methods_are_its_types():
    """T-0037: `extension Foo.Bar` gives its methods to `Bar` (`@receiver`, as Go's) without being a class itself: a
    type extended in several files stays one class, its references linked."""
    definitions, uses = _read(SWIFT, "Sources/e.swift", """\
        extension Foo.Bar: P {
            func k() { s() }
            init(n: Int) { self.init(a: n) }
            struct Inner { func f() {} }
        }
        extension Array where Element == UInt8 { func h() {} }
        """)
    assert definitions == {("method", "Bar.k", 2), ("method", "Bar.init", 3), ("class", "Inner", 4),
                           ("method", "Inner.f", 4), ("method", "Array.h", 6)}
    assert uses == {("reference", "P", 1, None), ("call", "s", 2, "Bar.k"), ("send", "init", 3, "Bar.init")}


def test_a_swift_defer_or_a_standard_function_libsignal_shadows_is_no_call():
    """T-0037: the grammar reads `defer { }` as a call `defer`; the standard `withUnsafePointer(to:)` (24 on
    libsignal) would be linked to libsignal's method of that name."""
    _, uses = _read(SWIFT, "Sources/d.swift", """\
        func f() {
            defer { g() }
            withUnsafePointer(to: 1) { _ in }
        }
        """)
    assert uses == {("call", "g", 2, "f")}


def test_a_kotlin_class_its_methods_and_its_calls():
    """libsignal (T-0038): a class, an interface, an enum and an `object` are classes, a companion object's functions
    its class's; a secondary constructor is the method `C.constructor`; an abstract function, an anonymous object's
    and a local one are no definitions. `b()` is a call, `x.c()`, `y?.z()` and `this.m()` are sends; a call to a
    capitalised name, `D(..)`, `Foo.Bar(..)`, `Array<Int>(..)`, and a supertype are references by the last name."""
    definitions, uses = _read(KOTLIN, "src/c.kt", """\
        class C(val x: Int) : B(), P, a.Q<Int> {
            constructor(y: String) : this(1) {
                b()
            }
            fun m(): Int {
                x.c(); y?.z(); Foo.Bar(1)
                val r = object : Runnable {
                    override fun run() { this@C.m() }
                }
                return D(2).k()
            }
            companion object {
                fun s() = C.s()
            }
        }
        interface P {
            fun v()
            fun w() {}
        }
        object O : P by d {
            private fun <T> o() { fun local() {} }
        }
        enum class E {
            A, B;
            fun e() {}
        }
        fun top() { listOf(1).map { it.u() }; Array<Int>(1) { 0 } }
        """)
    assert definitions == {("class", "C", 1), ("method", "C.constructor", 2), ("method", "C.m", 5),
                           ("method", "C.s", 13), ("class", "P", 16), ("method", "P.w", 18), ("class", "O", 20),
                           ("method", "O.o", 21), ("class", "E", 23), ("method", "E.e", 25), ("function", "top", 27)}
    assert uses == {("reference", "B", 1, "C"), ("reference", "P", 1, "C"), ("reference", "Q", 1, "C"),
                    ("call", "b", 3, "C.constructor"), ("send", "c", 6, "C.m"), ("send", "z", 6, "C.m"),
                    ("reference", "Bar", 6, "C.m"), ("reference", "Runnable", 7, "C.m"), ("send", "m", 8, "C.m"),
                    ("reference", "D", 10, "C.m"), ("send", "k", 10, "C.m"), ("send", "s", 13, "C.s"),
                    ("reference", "P", 20, "O"), ("call", "listOf", 27, "top"), ("send", "map", 27, "top"),
                    ("send", "u", 27, "top"), ("reference", "Array", 27, "top")}


def test_a_kotlin_extension_function_is_a_method_of_its_receiver():
    """T-0038: `fun Foo.Bar.f()` is the method `Bar.f` (`@receiver`, as Go's), so that libsignal's `toFfiArgType` of
    each type stay apart; nullable and generic receivers too."""
    definitions, _ = _read(KOTLIN, "src/e.kt", """\
        public fun UnauthProfileAuthorization.GroupSend.toFfiArgType() = 1
        suspend fun <T> CompletableFuture<T>.await(): T = get()
        fun Throwable?.toResult() {}
        class K {
            fun String.inside() {}
        }
        """)
    assert definitions == {("method", "GroupSend.toFfiArgType", 1), ("method", "CompletableFuture.await", 2),
                           ("method", "Throwable.toResult", 3), ("class", "K", 4), ("method", "String.inside", 5)}


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

    # not tolerant, so that the broken file is skipped and named (Go is tolerant since T-0039)
    go = graphe_generic.contribute(GO._replace(common=frozenset({"Get"}), tolerant=False), project)
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


def test_a_java_class_is_referenced_by_what_extends_and_builds_it_and_its_overloads_are_one_callee(tmp_path: Path):
    """protobuf (T-0033): `extends B` and `new B()` are `references` links; a call to `B`'s overloaded `o` is linked."""
    project = Project(tmp_path, {
        "b/B.java": """            class B {
                void o(int i) {}
                void o(String s) {}
            }
            """,
        "c/C.java": """            class C extends B {
                void m() {
                    new B();
                    o(1);
                }
            }
            """,
    })
    java = graphe_generic.contribute(JAVA, project)
    assert [n["id"] for n in java["nodes"] if n["kind"] == "method"] == ["b_b_java_b_o", "c_c_java_c_m"]
    assert {(e["source"], e["target"], e["relation"]) for e in java["links"] if e["relation"] != "contains"} == {
        ("c_c_java_c", "b_b_java_b", "references"), ("c_c_java_c_m", "b_b_java_b", "references"),
        ("c_c_java_c_m", "b_b_java_b_o", "calls")}


def test_a_cpp_call_to_a_c_function_is_linked_and_its_header_prototype_is_no_definition(tmp_path: Path):
    """protobuf (T-0034): `upb/arena.h` declares, `upb/arena.c` defines, a `.cc` calls; the `.h`'s struct and its
    inline method are read, its prototype is not a second `upb_Arena_New`."""
    project = Project(tmp_path, {
        "upb/arena.h": """\
            extern "C" {
            upb_Arena* upb_Arena_New(void);
            }
            struct Holder {
              void Reset() { upb_Arena_New(); }
            };
            """,
        "upb/arena.c": "upb_Arena* upb_Arena_New(void) { return 0; }\n",
        "src/user.cc": "void Use() { upb_Arena_New(); }\n",
    })
    c = graphe_generic.contribute(C, project)
    assert {(n["kind"], n["name"]) for n in c["nodes"] if n["kind"] != "file"} == {
        ("class", "Holder"), ("method", "Holder.Reset"), ("function", "upb_Arena_New"), ("function", "Use")}
    assert sorted((e["source"], e["target"]) for e in c["links"] if e["relation"] == "calls") == [
        ("src_user_cc_use", "upb_arena_c_upb_arena_new"), ("upb_arena_h_holder_reset", "upb_arena_c_upb_arena_new")]


def test_a_kotlin_call_to_a_java_method_is_linked_and_the_reverse(tmp_path: Path):
    """libsignal (T-0042): its Kotlin calls its Java's `nativeHandle`; Java calls a Kotlin top-level function through
    its file class (`FooKt.fromKotlin()`). `Foo.java` and `Foo.kt` keep their own ids."""
    project = Project(tmp_path, {
        "src/Foo.java": """\
            class Foo {
                long nativeHandle() { return 0; }
                void useKotlin() { FooKt.fromKotlin(); }
            }
            """,
        "src/Foo.kt": """\
            class Bar {
                fun m() {
                    Foo().nativeHandle()
                }
            }

            fun fromKotlin() {}
            """,
    })
    jvm = graphe_generic.contribute(JVM, project)
    ids = [n["id"] for n in jvm["nodes"]]
    assert "src_foo_java" in ids and "src_foo_kt" in ids and len(ids) == len(set(ids))
    assert {(e["source"], e["target"], e["relation"]) for e in jvm["links"] if e["relation"] != "contains"} == {
        ("src_foo_kt_bar_m", "src_foo_java_foo_nativehandle", "calls"),
        ("src_foo_kt_bar_m", "src_foo_java_foo", "references"),
        ("src_foo_java_foo_usekotlin", "src_foo_kt_fromkotlin", "calls")}


def test_two_nested_builders_of_one_file_are_two_nodes_and_a_call_both_define_is_ambiguous(tmp_path: Path):
    """protobuf (T-0043): `Foo.Builder.build` and `Bar.Builder.build` are two methods, so `build()` is linked to
    neither; a nested class is still referenced by its own name; `explain` designates it by either name."""
    project = Project(tmp_path, {
        "src/Msgs.java": """            class Foo {
                static class Builder {
                    Foo build() { return null; }
                }
            }

            class Bar {
                static class Builder {
                    Bar build() { return null; }
                }

                static class Only {}

                void use() {
                    build();
                    new Only();
                }
            }
            """,
    })
    java = graphe_generic.contribute(JAVA, project)
    names = {n["id"]: n["name"] for n in java["nodes"]}
    assert names["src_msgs_java_foo_builder"] == "Foo.Builder" and names["src_msgs_java_bar_builder"] == "Bar.Builder"
    assert names["src_msgs_java_foo_builder_build"] == "Foo.Builder.build"
    assert names["src_msgs_java_bar_builder_build"] == "Bar.Builder.build"
    links = {(e["source"], e["target"], e["relation"]) for e in java["links"]}
    assert ("src_msgs_java_foo_builder", "src_msgs_java_foo_builder_build", "contains") in links
    assert {(s, t, r) for s, t, r in links if r != "contains"} == {
        ("src_msgs_java_bar_use", "src_msgs_java_bar_only", "references")}
    assert {s["text"]: s["verdict"] for s in java["sites"]} == {"build": "ambiguous"}

    graph = nx.DiGraph()
    graph.add_nodes_from((n["id"], n) for n in java["nodes"])
    assert graphe.find(graph, "Foo.Builder.build") == ["src_msgs_java_foo_builder_build"]
    assert graphe.find(graph, "Builder.build") == ["src_msgs_java_bar_builder_build", "src_msgs_java_foo_builder_build"]
    assert graphe.find(graph, "Only") == ["src_msgs_java_bar_only"]
    assert graphe._designation(graph, "src_msgs_java_foo_builder_build") == "Foo.Builder.build"


def test_a_php_bare_call_is_linked_to_a_function_only_and_a_send_to_a_method_only(tmp_path: Path):
    """protobuf (T-0044): 219 bare calls to PHP's built-ins (`count()` 185, `substr()`, `pack()`) were linked to, or
    ambiguous with, protobuf's methods of that name; in PHP a bare `f()` is a function, `$x->f()` a method."""
    project = Project(tmp_path, {
        "a.php": """\
            <?php
            class Field { function count() {} function pack() {} }
            function pack() {}
            function caller($f) { count($f); $f->count(); pack(); $f->pack(); }
            """,
    })
    php = graphe_generic.contribute(PHP, project)
    calls = {(e["target"], e["source_location"]) for e in php["links"] if e["relation"] == "calls"}
    assert calls == {("a_php_field_count", "L4"), ("a_php_pack", "L4"), ("a_php_field_pack", "L4")}
    verdicts = {s["text"]: s["verdict"] for s in php["sites"]}
    assert verdicts == {"count": "external", "$f->count": "ours?", "pack": "ours?", "$f->pack": "ours?"}
