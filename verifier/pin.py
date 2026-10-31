from .checks import answer_key_problem, result


def verify_input(value):
    return result(True, "input is valid")


def verify_output(input_value, output_value, workspace):
    problem = answer_key_problem(input_value.puzzle_id, output_value)
    if problem:
        return result(False, problem)
    return result(True, "the answer key is the bundled puzzle, solved", optimal_cost=output_value.optimal_cost)
