extends CharacterBody2D
## Top-down player. Moves with the move_* input actions (WASD or arrow keys).

@export var speed := 220.0


func _physics_process(_delta: float) -> void:
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = direction * speed
	move_and_slide()
