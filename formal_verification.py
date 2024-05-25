def parse_xsb_to_model_data(xsb_input):
    model_data = {
        'boxes': [],
        'walls': [],
        'goals': [],
        'keeper_x': None,
        'keeper_y': None,
        'width': 0,
        'height': 0
    }
    keeper_position = None

    for line in xsb_input.split('\n'):
        line = line.strip()
        if not line:
            continue
        
        model_data['height'] += 1
        model_data['width'] = max(model_data['width'], len(line))
        y = model_data['height']

        for x, char in enumerate(line):
            x += 1
            if char == "$":
                model_data['boxes'].append((x, y))
            elif char == "*":
                model_data['boxes'].append((x, y))
                model_data['goals'].append((x, y))
            elif char == "#":
                model_data['walls'].append((x, y))
            elif char == ".":
                model_data['goals'].append((x, y))
            elif char == "@":
                keeper_position = (x, y)

    if keeper_position:
        model_data['keeper_x'], model_data['keeper_y'] = keeper_position
    else:
        raise ValueError("No keeper found in the input.")
        
    return model_data

def generate_init_wall(wall_positions, width, height):
    init_code = ""
    for x in range(width):
        for y in range(height):
            if ((x+1, y+1) in wall_positions):
                init_code += f"    init(wall[{x+1}][{y+1}]) := TRUE;\n"
            else:
                init_code += f"    init(wall[{x+1}][{y+1}]) := FALSE;\n"
    return init_code

def generate_init_goal(goal_positions, width, height):
    init_code = ""
    for x in range(width):
        for y in range(height):
            if ((x+1, y+1) in goal_positions):
                init_code += f"    init(goal[{x+1}][{y+1}]) := TRUE;\n"
            else:
                init_code += f"    init(goal[{x+1}][{y+1}]) := FALSE;\n"
    return init_code

def generate_init_boxes(boxes, width, height):
    init_boxes = ""

    for i in range(len(boxes)):
        for x in range(width):
            for y in range(height):
                if (boxes[i] == (x+1, y+1)):
                    init_boxes += f"    init(box_positions[{i+1}][{x+1}][{y+1}]) := TRUE;\n"
                else:
                    init_boxes += f"    init(box_positions[{i+1}][{x+1}][{y+1}]) := FALSE;\n"
                   
    return init_boxes

def generate_winning_condition(model_data):
    conditions = []
    
    for i, box in enumerate(model_data['boxes'], start=1):
        condition = " |\n         ".join([f"(box_positions[{i}][{goal_x}][{goal_y}] = TRUE)" 
                                          for goal_x, goal_y in model_data['goals']])
        conditions.append(f"{condition}")
    return ("!F ((" + " ) &\n (    ".join(conditions) + "))")

def generate_transition_conditions(model_data, num_boxes):
    transitions = "(\n"
    keeper_box_transitions = ""
    default_movements = ""    

    keeper_transitions = f"""
    -- ** Keeper movements without boxes **
    -- Keeper moves left
    keeper_x > 1 & !wall[keeper_x - 1][keeper_y] & 
    {' & '.join(f'!box_positions[{j}][keeper_x - 1][keeper_y]' for j in range(1, num_boxes + 1))} : 
        next(keeper_x) = keeper_x - 1 &
        next(keeper_y) = keeper_y &
    {' & '.join(f'next(wall[{x}][{y}]) = wall[{x}][{y}]' 
                for x in range(1, model_data['width'] + 1) 
                for y in range(1, model_data['height'] + 1))} &
    {' & '.join(f'next(goal[{x}][{y}]) = goal[{x}][{y}]' 
                for x in range(1, model_data['width'] + 1) 
                for y in range(1, model_data['height'] + 1))} &
    {' & '.join(f'next(box_positions[{j}][{x}][{y}]) = box_positions[{j}][{x}][{y}]' 
                for j in range(1, num_boxes + 1) 
                for x in range(1, model_data['width']) 
                for y in range(1, model_data['height']))};

    -- Keeper moves right
    keeper_x < {model_data['width'] + 1} & !wall[keeper_x + 1][keeper_y] & 
    {' & '.join(f'!box_positions[{j}][keeper_x + 1][keeper_y]' for j in range(1, num_boxes + 1))} : 
        next(keeper_x) = keeper_x + 1 &
        next(keeper_y) = keeper_y &
        {' & '.join(f'next(wall[{x}][{y}]) = wall[{x}][{y}]' 
                for x in range(1, model_data['width'] + 1) 
                for y in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(goal[{x}][{y}]) = goal[{x}][{y}]' 
                    for x in range(1, model_data['width'] + 1) 
                    for y in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(box_positions[{j}][{x}][{y}]) = box_positions[{j}][{x}][{y}]' 
                    for j in range(1, num_boxes + 1) 
                    for x in range(1, model_data['width']) 
                    for y in range(1, model_data['height']))};

    -- Keeper moves up
    keeper_y > 1 & !wall[keeper_x][keeper_y - 1] & 
    {' & '.join(f'!box_positions[{j}][keeper_x][keeper_y - 1]' for j in range(1, num_boxes + 1))} : 
        next(keeper_x) = keeper_x &
        next(keeper_y) = keeper_y - 1 &
        {' & '.join(f'next(wall[{x}][{y}]) = wall[{x}][{y}]' 
                for x in range(1, model_data['width'] + 1) 
                for y in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(goal[{x}][{y}]) = goal[{x}][{y}]' 
                    for x in range(1, model_data['width'] + 1) 
                    for y in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(box_positions[{j}][{x}][{y}]) = box_positions[{j}][{x}][{y}]' 
                    for j in range(1, num_boxes + 1) 
                    for x in range(1, model_data['width']) 
                    for y in range(1, model_data['height']))};

    -- Keeper moves down
    keeper_y < {model_data['height'] + 1} & !wall[keeper_x][keeper_y + 1] & 
    {' & '.join(f'!box_positions[{j}][keeper_x][keeper_y + 1]' for j in range(1, num_boxes + 1))} : 
        next(keeper_x) = keeper_x &
        next(keeper_y) = keeper_y + 1 &
        {' & '.join(f'next(wall[{x}][{y}]) = wall[{x}][{y}]' 
                for x in range(1, model_data['width'] + 1) 
                for y in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(goal[{x}][{y}]) = goal[{x}][{y}]' 
                    for x in range(1, model_data['width'] + 1) 
                    for y in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(box_positions[{j}][{x}][{y}]) = box_positions[{j}][{x}][{y}]' 
                    for j in range(1, num_boxes + 1) 
                    for x in range(1, model_data['width']) 
                    for y in range(1, model_data['height']))};
    """

    for i in range(1, num_boxes + 1):
        for x in range(1, model_data['width'] - 1):
            for y in range(1, model_data['height'] + 1):
                keeper_box_transitions += f"""

    -- ** Handling box movements when keeper pushes box[{i}] right from position ({x},{y})**
    keeper_x = {x} & !wall[{x + 1}][{y}] & !wall[{x + 2}][{y}] & 
    box_positions[{i}][{x + 1}][{y}] & !goal[{x + 1}][{y}] {'&' if (num_boxes > 1) else ''} 
    {' & '.join(f'!box_positions[{j}][{x + 2}][{y}]' for j in range(1, num_boxes + 1) if j != i)} : 
        next(box_positions[{i}][{x + 1}][{y}]) = FALSE &
        next(box_positions[{i}][{x + 2}][{y}]) = TRUE &
        next(keeper_x) = {x + 1} &
        next(keeper_y) = {y} &
        {' & '.join(f'next(wall[{wx}][{wy}]) = wall[{wx}][{wy}]' 
                    for wx in range(1, model_data['width'] + 1) 
                    for wy in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(goal[{gx}][{gy}]) = goal[{gx}][{gy}]' 
                    for gx in range(1, model_data['width'] + 1) 
                    for gy in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(box_positions[{j}][{bx}][{by}]) = box_positions[{j}][{bx}][{by}]'
                    for j in range(1, num_boxes + 1) 
                    for bx in range(1, model_data['width'] + 1)
                    for by in range(1, model_data['height'] + 1)
                    if not (i == j and (bx == x + 2 or bx == x + 1) and (by == y)))};
        """

    for i in range(1, num_boxes + 1):
        for x in range(3, model_data['width'] + 1):
            for y in range(1, model_data['height'] + 1):
                keeper_box_transitions += f"""

    -- ** Handling box movements when keeper pushes box[{i}] left from position ({x},{y})**
    keeper_x = {x} & !wall[{x - 1}][{y}] & !wall[{x - 2}][{y}] & 
    box_positions[{i}][{x - 1}][{y}] & !goal[{x - 1}][{y}] {'&' if (num_boxes > 1) else ''} 
    {' & '.join(f'!box_positions[{j}][{x - 2}][{y}]' for j in range(1, num_boxes + 1) if j != i)} : 
        next(box_positions[{i}][{x - 1}][{y}]) = FALSE &
        next(box_positions[{i}][{x - 2}][{y}]) = TRUE &
        next(keeper_x) = {x - 1} &
        next(keeper_y) = {y} &
        {' & '.join(f'next(wall[{wx}][{wy}]) = wall[{wx}][{wy}]' 
                    for wx in range(1, model_data['width'] + 1) 
                    for wy in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(goal[{gx}][{gy}]) = goal[{gx}][{gy}]' 
                    for gx in range(1, model_data['width'] + 1) 
                    for gy in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(box_positions[{j}][{bx}][{by}]) = box_positions[{j}][{bx}][{by}]'
                    for j in range(1, num_boxes + 1) 
                    for bx in range(1, model_data['width'] + 1)
                    for by in range(1, model_data['height'] + 1)
                    if not (i == j and (bx == x - 2 or bx == x - 1) and (by == y)))};
        """

    for i in range(1, num_boxes + 1):
        for y in range(3, model_data['height'] + 1):
            for x in range(1, model_data['width'] + 1):
                keeper_box_transitions += f"""

    -- ** Handling box movements when keeper pushes box[{i}] up from position ({x},{y})**
    keeper_y = {y} & !wall[{x}][{y - 1}] & !wall[{x}][{y - 2}] & 
    box_positions[{i}][{x}][{y - 1}] & !goal[{x}][{y - 1}] {'&' if (num_boxes > 1) else ''} 
    {' & '.join(f'!box_positions[{j}][{x}][{y - 2}]' for j in range(1, num_boxes + 1) if j != i)} : 
        next(box_positions[{i}][{x}][{y - 1}]) = FALSE &
        next(box_positions[{i}][{x}][{y - 2}]) = TRUE &
        next(keeper_x) = {x} &
        next(keeper_y) = {y - 1} &
        {' & '.join(f'next(wall[{wx}][{wy}]) = wall[{wx}][{wy}]' 
                    for wx in range(1, model_data['width'] + 1) 
                    for wy in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(goal[{gx}][{gy}]) = goal[{gx}][{gy}]' 
                    for gx in range(1, model_data['width'] + 1) 
                    for gy in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(box_positions[{j}][{bx}][{by}]) = box_positions[{j}][{bx}][{by}]'
                    for j in range(1, num_boxes + 1) 
                    for bx in range(1, model_data['width'] + 1)
                    for by in range(1, model_data['height'] + 1)
                    if not (i == j and (by == y - 2 or by == y - 1) and (bx == x)))};
        """

    for i in range(1, num_boxes + 1):
        for y in range(1, model_data['height'] - 1):
            for x in range(1, model_data['width'] + 1):
                keeper_box_transitions += f"""

    -- ** Handling box movements when keeper pushes box[{i}] down from position ({x},{y})**
    keeper_y = {y} & !wall[{x}][{y + 1}] & !wall[{x}][{y + 2}] & 
    box_positions[{i}][{x}][{y + 1}] & !goal[{x}][{y + 1}] {'&' if (num_boxes > 1) else ''} 
    {' & '.join(f'!box_positions[{j}][{x}][{y + 2}]' for j in range(1, num_boxes + 1) if j != i)} : 
        next(box_positions[{i}][{x}][{y + 1}]) = FALSE &
        next(box_positions[{i}][{x}][{y + 2}]) = TRUE &
        next(keeper_x) = {x} &
        next(keeper_y) = {y + 1} &
        {' & '.join(f'next(wall[{wx}][{wy}]) = wall[{wx}][{wy}]' 
                    for wx in range(1, model_data['width'] + 1) 
                    for wy in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(goal[{gx}][{gy}]) = goal[{gx}][{gy}]' 
                    for gx in range(1, model_data['width'] + 1) 
                    for gy in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(box_positions[{j}][{bx}][{by}]) = box_positions[{j}][{bx}][{by}]'
                    for j in range(1, num_boxes + 1) 
                    for bx in range(1, model_data['width'] + 1)
                    for by in range(1, model_data['height'] + 1)
                    if not (i == j and (by == y + 2 or by == y + 1) and (bx == x)))};
        """    
    default_movements += f"""
    -- Default: No movement
    TRUE : 
        next(keeper_x) = keeper_x &
        next(keeper_y) = keeper_y &
        {' & '.join(f'next(wall[{x}][{y}]) = wall[{x}][{y}]' for x in range(1, model_data['width'] + 1) for y in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(goal[{x}][{y}]) = goal[{x}][{y}]' for x in range(1, model_data['width'] + 1) for y in range(1, model_data['height'] + 1))} &
        {' & '.join(f'next(box_positions[{j}][{x}][{y}]) = box_positions[{j}][{x}][{y}]' for j in range(1, num_boxes + 1) for x in range(1, model_data['width'] + 1) for y in range(1, model_data['height'] + 1))};
    """
        
    transitions = f"case\n{keeper_transitions}\n{keeper_box_transitions}\n{default_movements}\nesac;\n"
    return transitions

def generate_smv_model(model_data):
    num_boxes = len(model_data['boxes'])
    width = model_data['width']
    height = model_data['height']
    max_index = num_boxes

    # Define the SMV model structure
    smv_model = "MODULE main\n"
    smv_model += f"VAR\n"
    smv_model += f"    keeper_x : 1..{width};\n"
    smv_model += f"    keeper_y : 1..{height};\n"
    smv_model += f"    wall : array 1..{width} of array 1..{height} of boolean;\n"
    smv_model += f"    goal : array 1..{width} of array 1..{height} of boolean;\n"
    smv_model += f"    box_positions : array 1..{max_index} of array 1..{width} of array 1..{height} of boolean;\n"

    # Assign initial states using provided functions
    smv_model += "ASSIGN\n"
    smv_model += f"    init(keeper_x) := {model_data['keeper_x']};\n"
    smv_model += f"    init(keeper_y) := {model_data['keeper_y']};\n"
    smv_model += generate_init_wall(model_data['walls'], width, height)
    smv_model += generate_init_goal(model_data['goals'], width, height)
    smv_model += generate_init_boxes(model_data['boxes'], width, height)

    # Transitions and LTL Specifications
    smv_model += f"TRANS\n    {generate_transition_conditions(model_data, num_boxes)}\n"
    smv_model += f"LTLSPEC\n    {generate_winning_condition(model_data)}\n"

    return smv_model

if __name__ == "__main__":
    xsb_input = """
    ###
    #@#
    #$#
    #.#
    ###
    """

    model_data = parse_xsb_to_model_data(xsb_input)
    smv_model = generate_smv_model(model_data)

    # Save the smv_model to a file
    filename = f'C:\\nuXmv-2.0.0-win64\\bin\\sokoban.smv'
    with open(filename, 'w') as smv_file:
        smv_file.write(smv_model)

    print("Done.")
