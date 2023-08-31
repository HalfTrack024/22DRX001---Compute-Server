class Parse_Progress:

    def __init__(self):
        self.panels_total = 0
        self.panels_interior = 0
        self.panels_exterior = 0
        self.stud_type_required: list = []
        self.sheathing_type_required: list = []


class Build_EC1_Progress:
    fm3_status: str
    sf3_status: str
    auto_stud_type: str
    auto_stud_count: int
    sub_assembly_count: int
    fasteners_required: list
    materials_required: list

    def __init__(self):
        self.fm3_status = 'Not-Started'
        self.sf3_status = 'Not-Started'
        self.auto_stud_type = 'Unknown'
        self.auto_stud_count = 0
        self.sub_assembly_count = 0
        self.fasteners_required: list = []
        self.materials_required: list = []


class Build_RBC_Progress:

    def __init__(self):
        self.ec2_status = 'Not-Started'
        self.ec3_status = 'Not-Started'
        self.ec2_operations: list = []
        self.ec3_operations: list = []
        self.fasteners_required: list = []
        self.materials_required: list = []
        self.material_count = 0
