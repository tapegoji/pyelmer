"""Wrapper for Elmer simulation input file (sif-file).

The sif file is represented by a Simulation object, which contains
dictionaries of objects for each section (i.e. Solvers, Bodies, 
Materials, etc.).
Each of these objects contains the data required in the sif in form
of a dictionary called data.
"""

import os
import yaml


data_dir = "./"


class Simulation:
    """Main wrapper for the sif file. The simulation class is used to
    collect all information.
    In the end, it writes the sif-file.
    """

    def __init__(self):
        self.intro_text = ""
        self.header = {
            "CHECK KEYWORDS": '"Warn"',
            "Mesh DB": '"." "."',
        }
        self.materials = {}
        self.bodies = {}
        self.boundaries = {}
        self.next_bndry_id = 1
        self.body_forces = {}
        self.components = {}
        self.initial_conditions = {}
        self.solvers = {}
        self.equations = {}
        self.constants = {"Stefan Boltzmann": 5.6704e-08}
        self.settings = {}
        self.sif_filename = "case.sif"        

    def write_sif(self, simulation_dir):
        """Write sif file.

        Args:
            simulation_dir (str): Path of simulation directory
        """
        self._set_ids()
        with open(os.path.join(simulation_dir, self.sif_filename), "w") as f:
            if self.intro_text != "":
                f.write(self.intro_text)
                f.write("\n\n")
            f.write("Header\n")
            f.write(self._dict_to_str(self.header, key_value_separator=" "))
            f.write("End\n\n")
            f.write("Simulation\n")
            f.write(self._dict_to_str(self.settings))
            f.write("End\n\n")
            f.write("Constants\n")
            f.write(self._dict_to_str(self.constants))
            f.write("End\n\n")
            for equation_name, equation in self.equations.items():
                f.write("! " + equation_name + "\n")
                f.write("Equation " + str(equation.id) + "\n")
                f.write(self._dict_to_str(equation.get_data()))
                f.write("End\n\n")
            f.write("\n")
            for solver_name, solver in self.solvers.items():
                f.write("! " + solver_name + "\n")
                f.write("Solver " + str(solver.id) + "\n")
                f.write(self._dict_to_str(solver.get_data()))
                f.write("End\n\n")
            f.write("\n")
            for material_name, material in self.materials.items():
                f.write("! " + material_name + "\n")
                f.write("Material " + str(material.id) + "\n")
                f.write(self._dict_to_str(material.get_data()))
                f.write("End\n\n")
            f.write("\n")
            for body_name, body in self.bodies.items():
                f.write("! " + body_name + "\n")
                f.write("Body " + str(body.id) + "\n")
                f.write(self._dict_to_str(body.get_data()))
                f.write("End\n\n")
            f.write("\n")
            for boundary_name, boundary in self.boundaries.items():
                f.write("! " + boundary_name + "\n")
                f.write("Boundary Condition " + str(boundary.id) + "\n")
                f.write(self._dict_to_str(boundary.get_data()))
                f.write("End\n\n")
            f.write("\n")
            for body_force_name, body_force in self.body_forces.items():
                f.write("! " + body_force_name + "\n")
                f.write("Body Force " + str(body_force.id) + "\n")
                f.write(self._dict_to_str(body_force.get_data()))
                f.write("End\n\n")
            f.write("\n")
            for component_name, component in self.components.items():
                f.write("! " + component_name + "\n")
                f.write("Component " + str(component.id) + "\n")
                f.write(self._dict_to_str(component.get_data()))
                f.write("End\n\n")
            f.write("\n")
            for (
                initial_condition_name,
                initial_condition,
            ) in self.initial_conditions.items():
                f.write("! " + initial_condition_name + "\n")
                f.write("Initial Condition " + str(initial_condition.id) + "\n")
                f.write(self._dict_to_str(initial_condition.get_data()))
                f.write("End\n\n")
        print("Wrote sif-file.")

    def write_startinfo(self, simulation_dir):
        """Write ELMERSOLVER_STARTINFO file in simulation directory.

        Args:
            simulation_dir (str): simulation directory
        """
        with open(os.path.join(simulation_dir, "ELMERSOLVER_STARTINFO"), "w") as f:
            f.write(self.sif_filename)
            f.write("\n")

    def write_boundary_ids(self, simulation_dir):
        """Write yaml-file containing the boundary names and the
        assigned elmer body-ids.

        Args:
            simulation_dir (str): Path of simulation directory
        """
        data = {boundary.id: name for name, boundary in self.boundaries.items()}
        with open(os.path.join(simulation_dir, "boundaries.yml"), "w") as f:
            yaml.dump(data, f, sort_keys=False)

    def _dict_to_str(self, dictionary, *, key_value_separator=" = "):
        text = ""
        for key, value in dictionary.items():
            text = "".join([text, "  ", key, key_value_separator, str(value), "\n"])
        return text

    def _set_ids(self):
        objects = [
            self.solvers,
            self.equations,
            self.materials,
            self.bodies,
            # self.boundaries,
            self.body_forces,
            self.components,
            self.initial_conditions,
        ]
        # give each object id
        for obj in objects:
            id_ = 1
            for key in obj:
                obj[key].id = id_
                id_ += 1


class Body:
    """Wrapper for bodies in sif-file."""

    def __new__(cls, simulation, name, body_ids=None, data=None):
        """Intercept object construction to return an existing object if possible."""
        if name in simulation.bodies:
            existing = simulation.bodies[name]
            new_body_ids = [] if body_ids is None else body_ids
            new_data = {} if data is None else data
            if [new_body_ids, new_data] != [existing.body_ids, existing.data]:
                raise ValueError(f'Body name clash: "{name}".')
            return existing
        else:
            return super().__new__(cls)

    def __init__(self, simulation, name, body_ids=None, data=None):
        """Create body object.

        Args:
            simulation (Simulation Object): The body is added to this
                                            simulation object.
            name (str): Name of the body
            body_ids (list of int): Ids of bodies in mesh.
            data (dict, optional): Body data as in sif-file.
        """
        simulation.bodies.update({name: self})
        self.id = 0
        self.name = name
        if body_ids is None:
            self.body_ids = []
        else:
            self.body_ids = body_ids
        if data is None:
            self.data = {}
        else:
            self.data = data
        # optional parameters
        self.equation = None  # : optional reference to an Equation object
        self.initial_condition = (
            None  # : optional reference to an InitialCondition object
        )
        self.material = None  # : optional reference to a Material object
        self.body_force = None  # : optional reference to a BodyForce object

    def get_data(self):
        """Generate dictionary with data for sif-file."""
        d = {
            f"Target Bodies({len(self.body_ids)})": " ".join(
                [str(x) for x in self.body_ids]
            )
        }
        if self.equation is not None:
            d.update({"Equation": f"{self.equation.id}  ! {self.equation.name}"})
        if self.initial_condition is not None:
            d.update(
                {
                    "Initial Condition": f"{self.initial_condition.id}  ! {self.initial_condition.name}"
                }
            )
        if self.material is not None:
            d.update({"Material": f"{self.material.id}  ! {self.material.name}"})
        if self.body_force is not None:
            d.update({"Body Force": f"{self.body_force.id}  ! {self.body_force.name}"})
        d.update(self.data)
        return d

    def __str__(self):
        return str(self.id)


class Boundary:
    """Wrapper for boundaries in sif-file."""

    def __new__(cls, simulation, name, geo_ids=None, data=None):
        """Intercept object construction to return an existing object if possible."""
        if name in simulation.boundaries:
            existing = simulation.boundaries[name]
            new_geo_ids = [] if geo_ids is None else geo_ids
            new_data = {} if data is None else data
            if [new_geo_ids, new_data] != [existing.geo_ids, existing.data]:
                raise ValueError(f'Boundary name clash: "{name}".')
            return existing
        else:
            return super().__new__(cls)

    def __init__(self, simulation, name, geo_ids=None, data=None):
        """Create boundary object.

        Args:
            simulation (Simulation Object): The boundary is added to
                                            this simulation object.
            name (str): Name of the body
            surf_ids (list of int, optional): Ids of boundaries in mesh.
            data (dict, optional): Boundary data as in sif-file.
        """
        simulation.boundaries.update({name: self})
        self.id = simulation.next_bndry_id
        simulation.next_bndry_id += 1
        self.name = name
        if geo_ids is None:
            self.geo_ids = []
        else:
            self.geo_ids = geo_ids
        if data is None:
            self.data = {}
        else:
            self.data = data

    def get_data(self):
        """Generate dictionary with data for sif-file."""
        d = {
            f"Target Boundaries({len(self.geo_ids)})": " ".join(
                [str(x) for x in self.geo_ids]
            )
        }
        d.update(self.data)
        return d

    def __str__(self):
        return str(self.id)


class Material:
    """Wrapper for materials in sif-file."""

    def __new__(cls, simulation, name, data=None):
        """Intercept object construction to return an existing object if possible."""
        if name in simulation.materials:
            existing = simulation.materials[name]
            new_data = {} if data is None else data
            if new_data != existing.data:
                raise ValueError(f'Material name clash: "{name}".')
            return existing
        else:
            return super().__new__(cls)

    def __init__(self, simulation, name, data=None):
        """Create material object

        Args:
            simulation (Simulation Object): The material is added to
                                            this simulation object.
            name (str): Name of the material
            data (dict, optional): Material data as in sif-file.
        """
        simulation.materials.update({name: self})
        self.id = 0
        self.name = name
        if data is None:
            self.data = {}
        else:
            self.data = data

    def get_data(self):
        """Generate dictionary with data for sif-file."""
        return self.data

    def __str__(self):
        return str(self.id)


class BodyForce:
    """Wrapper for body forces in sif-file."""

    def __new__(cls, simulation, name, data=None):
        """Intercept object construction to return an existing object if possible."""
        if name in simulation.body_forces:
            existing = simulation.body_forces[name]
            new_data = {} if data is None else data
            if new_data != existing.data:
                raise ValueError(f'BodyForce name clash: "{name}".')
            return existing
        else:
            return super().__new__(cls)

    def __init__(self, simulation, name, data=None):
        """Create body force object.

        Args:
            simulation (Simulation Object): The body force is added to
                                            this simulation object.
            name (str): Name of the body force
            data (dict, optional): Body force data as in sif-file.
        """
        simulation.body_forces.update({name: self})
        self.id = 0
        self.name = name
        if data is None:
            self.data = {}
        else:
            self.data = data

    def get_data(self):
        """Generate dictionary with data for sif-file."""
        return self.data

    def __str__(self):
        return str(self.id)


class Component:
    """Wrapper for components in sif-file."""

    def __new__(
        cls, simulation, name, master_bodies=None, master_boundaries=None, data=None
    ):
        """Intercept object construction to return an existing object if possible."""
        if name in simulation.components:
            existing = simulation.components[name]
            new_master_bodies = [] if master_bodies is None else master_bodies
            new_master_boundaries = (
                [] if master_boundaries is None else master_boundaries
            )
            new_data = {} if data is None else data
            if [new_master_bodies, new_master_boundaries, new_data] != [
                existing.master_bodies,
                existing.master_boundaries,
                existing.data,
            ]:
                raise ValueError(f'Component name clash: "{name}".')
            return existing
        else:
            return super().__new__(cls)

    def __init__(
        self, simulation, name, master_bodies=None, master_boundaries=None, data=None
    ):
        """Create component object.

        Args:
            simulation (Simulation Object): The component is added to
                                            this simulation object.
            name (str): Name of the component
            master_bodies (list of Body, optional): Master Body objects.
            master_bodies (list of Boundary, optional): Master Boundary objects.
            data (dict, optional): Component data as in sif-file.
        """
        simulation.components.update({name: self})
        self.id = 0
        self.name = name
        if master_bodies is None:
            self.master_bodies = []
        else:
            self.master_bodies = master_bodies
        if master_boundaries is None:
            self.master_boundaries = []
        else:
            self.master_boundaries = master_boundaries
        if data is None:
            self.data = {}
        else:
            self.data = data

    def get_data(self):
        """Generate dictionary with data for sif-file."""
        d = {
            "Name": self.name,
        }
        if self.master_bodies != []:
            body_names = ""
            for body in self.master_bodies:
                body_names += f"{body.name}, "
            body_names = body_names.strip()
            d.update(
                {
                    f"Master Bodies({len(self.master_bodies)})": f"{' '.join([str(x) for x in self.master_bodies])}  ! {body_names}"
                }
            )
        if self.master_boundaries != []:
            boundary_names = ""
            for boundary in self.master_boundaries:
                boundary_names += f"{boundary.name}, "
            boundary_names = boundary_names.strip()
            d.update(
                {
                    f"Master Boundaries({len(self.master_boundaries)})": f"{' '.join([str(x) for x in self.master_boundaries])}  ! {boundary_names}"
                }
            )
        d.update(self.data)
        return d

    def __str__(self):
        return str(self.id)


class InitialCondition:
    """Wrapper for initial condition in sif-file."""

    def __new__(cls, simulation, name, data=None):
        """Intercept object construction to return an existing object if possible."""
        if name in simulation.initial_conditions:
            existing = simulation.initial_conditions[name]
            new_data = {} if data is None else data
            if new_data != existing.data:
                raise ValueError(f'InitialCondition name clash: "{name}".')
            return existing
        else:
            return super().__new__(cls)

    def __init__(self, simulation, name, data=None):
        """Create initial condition object.

        Args:
            simulation (Simulation Object): The initial condition is
                                            added to this simulation
                                            object.
            name (str): Name of the initial condition
            data (dict, optional): Initial condition data as in sif-file.
        """
        simulation.initial_conditions.update({name: self})
        self.id = 0
        self.name = name
        if data is None:
            self.data = {}
        else:
            self.data = data

    def get_data(self):
        """Generate dictionary with data for sif-file."""
        return self.data

    def __str__(self):
        return str(self.id)


class Solver:
    """Wrapper for solver in sif-file."""

    def __new__(cls, simulation, name, data=None):
        """Intercept object construction to return an existing object if possible."""
        if name in simulation.solvers:
            existing = simulation.solvers[name]
            new_data = {} if data is None else data
            if new_data != existing.data:
                raise ValueError(f'Solver name clash: "{name}".')
            return existing
        else:
            return super().__new__(cls)

    def __init__(self, simulation, name, data=None):
        """Create solver object

        Args:
            simulation (Simulation Object): The solver is added to
                                            this simulation object.
            name (str): Name of the solver
            data (dict, optional): Solver data as in sif-file.
        """
        simulation.solvers.update({name: self})
        self.id = 0
        self.name = name
        if data is None:
            self.data = {}
        else:
            self.data = data

    def get_data(self):
        """Generate dictionary with data for sif-file."""
        return self.data

    def __str__(self):
        return str(self.id)


class Equation:
    """Wrapper for equations in sif-file."""

    def __new__(cls, simulation, name, solvers, data=None):
        """Intercept object construction to return an existing object if possible."""
        if name in simulation.equations:
            existing = simulation.equations[name]
            new_data = {} if data is None else data
            if [solvers, new_data] != [existing.solvers, existing.data]:
                raise ValueError(f'Equation name clash: "{name}".')
            return existing
        else:
            return super().__new__(cls)

    def __init__(self, simulation, name, solvers, data=None):
        """Create equation object

        Args:
            simulation (Simulation Object): The equation is added to
                                            this simulation object.
            name (str): Name of the equation
            solvers ([list]): Solvers in this equation
            data (dict, optional): Equation data as in sif-file.
        """
        simulation.equations.update({name: self})
        self.id = 0
        self.name = name
        self.solvers = solvers
        if data is None:
            self.data = {}
        else:
            self.data = data

    def get_data(self):
        """Generate dictionary with data for sif-file."""
        solver_id_str = ""
        solver_name_str = ""
        for solver in self.solvers:
            solver_id_str += f"{solver.id} "
            solver_name_str += f"{solver.name}, "
        d = {
            f"Active Solvers({len(self.solvers)})": f"{solver_id_str}  ! {solver_name_str}"
        }
        d.update(self.data)
        return d

    def __str__(self):
        return str(self.id)


class StringFromList:
    """String including references to other Bodies, Boundaries, ..."""

    def __init__(self, content: list):
        """Create StringWithReference object.

        Args:
            content (list): The content of the string, separated into
            text, bodies / boundaries, ....
            e.g. ["integer", boundary1]; type(boundary1)=elmer.Boundary
        """
        self.content = content

    def __str__(self):
        """This is evaluated when writing the sif, when the IDs have
        already been assigned."""
        return " ".join([str(x) for x in self.content])


def load_simulation(name, setup_file=""):
    """Load simulation settings from database.

    Args:
        name (str): Name of the simulation in database.
        setup_file (str, optional): Path to yaml file cotaining setup.

    Returns:
        Simulation object.
    """
    if setup_file == "":
        setup_file = os.path.join(data_dir, "simulations.yml")
    with open(setup_file) as f:
        settings = yaml.safe_load(f)[name]
    sim = Simulation()
    sim.settings = settings
    return sim


def load_material(name, simulation, setup_file=""):
    """Load material from data base and add it to simulation.

    Args:
        name (str): material name
        simulation (Simulation object)
        setup_file (str, optional): Path to yaml file cotaining setup.

    Returns:
        Material object.
    """
    if setup_file == "":
        setup_file = os.path.join(data_dir, "materials.yml")
    with open(setup_file) as f:
        data = yaml.safe_load(f)[name]
    return Material(simulation, name, data)


def load_solver(name, simulation, setup_file=""):
    """Load solver from data base and add it to simulation.

    Args:
        name (str): solver name
        simulation (Simulation object)
        setup_file (str, optional): Path to yaml file cotaining setup.

    Returns:
        Solver object.
    """
    if setup_file == "":
        setup_file = os.path.join(data_dir, "solvers.yml")
    with open(setup_file) as f:
        data = yaml.safe_load(f)[name]
    return Solver(simulation, name, data)


def load_boundary(name, simulation, setup_file=""):
    """Load boundary from data base and add it to simulation.

    Args:
        name (str): boundary name
        simulation (Simulation object)
        setup_file (str, optional): Path to yaml file cotaining setup.

    Returns:
        Boundary object.
    """
    if setup_file == "":
        setup_file = os.path.join(data_dir, "boundaries.yml")
    with open(setup_file) as f:
        data = yaml.safe_load(f)[name]
    return Boundary(simulation, name, data=data)


def load_initial_condition(name, simulation, setup_file=""):
    """Load initial condition from data base and add it to simulation.

    Args:
        name (str): initial condition name
        simulation (Simulation object)
        setup_file (str, optional): Path to yaml file cotaining setup.

    Returns:
        InitialCondition object.
    """
    if setup_file == "":
        setup_file = os.path.join(data_dir, "initial_conditions.yml")
    with open(setup_file) as f:
        data = yaml.safe_load(f)[name]
    return InitialCondition(simulation, name, data)


def load_body_force(name, simulation, setup_file=""):
    """Load body force from data base and add it to simulation.

    Args:
        name (str): body force name
        simulation (Simulation object)
        setup_file (str, optional): Path to yaml file cotaining setup.

    Returns:
        BodyForce object.
    """
    if setup_file == "":
        setup_file = os.path.join(data_dir, "body_forces.yml")
    with open(setup_file) as f:
        data = yaml.safe_load(f)[name]
    return BodyForce(simulation, name, data)
