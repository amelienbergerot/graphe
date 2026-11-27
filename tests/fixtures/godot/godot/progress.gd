class_name Progress
extends Node

signal saved

const MAX := 3
var score := 0


func record(points: int) -> void:
	score += points
	_save()


func _save() -> void:
	saved.emit()


func reset() -> void:
	score = 0
