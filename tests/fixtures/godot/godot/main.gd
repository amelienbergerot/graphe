extends Node

const Prog = preload("res://progress.gd")


func _ready() -> void:
	var p: Prog = Prog.new()
	p.saved.connect(_on_saved)
	p.record(Prog.MAX)
	add_child(p)
	Prog.record(1)
	var other = get_node("Other")
	other.reset()


func _on_saved() -> void:
	pass
