# SPDX-License-Identifier: BSD-3-Clause

import numpy as np


# This is your team name
CREATOR = "Bumblebeeeeee"

COMPETING_MINE_RADIUS = 40


# This is the AI bot that will be instantiated for the competition
class PlayerAi:

    def __init__(self):
        self.team = CREATOR  # Mandatory attribute

        # Record the previous positions of all my vehicles
        self.previous_positions = {}
        # Record the number of tanks and ships I have at each base
        self.ntanks = {}
        self.nships = {}

    def get_closest_base(self, base, bases):
        """
        Returns the closest base to the given base.
        """
        closest_base = None
        closest_distance = np.inf
        for base_item in bases:
            if base_item.uid != base.uid:

                distance = np.linalg.norm(np.array((base_item.x, base_item.x)) - np.array((base.x, base.y)))  # TODO: count distance through edges
                # print(f'{distance = }')
                if distance < closest_distance:
                    closest_base = base_item
                    closest_distance = distance
        return closest_base

    def run(self, t: float, dt: float, info: dict, game_map: np.ndarray):
        """
        This is the main function that will be called by the game engine.

        Parameters
        ----------
        t : float
            The current time in seconds.
        dt : float
            The time step in seconds.
        info : dict
            A dictionary containing all the information about the game.
            The structure is as follows:
            {
                "team_name_1": {
                    "bases": [base_1, base_2, ...],
                    "tanks": [tank_1, tank_2, ...],
                    "ships": [ship_1, ship_2, ...],
                    "jets": [jet_1, jet_2, ...],
                },
                "team_name_2": {
                    ...
                },
                ...
            }
        game_map : np.ndarray
            A 2D numpy array containing the game map.
            1 means land, 0 means water, -1 means no info.
        """

        # Get information about my team
        myinfo = info[self.team]

        # Controlling my bases =================================================

        # Iterate through all my bases (vehicles belong to bases)
        for base in myinfo["bases"]:
            # If this is a new base, initialize the tank & ship counters
            if base.uid not in self.ntanks:
                self.ntanks[base.uid] = 0
            if base.uid not in self.nships:
                self.nships[base.uid] = 0
            # Firstly, each base should build a mine if it has less than 3 mines
            if base.mines < 3:
                if base.crystal > base.cost("mine"):
                    base.build_mine()
            # Secondly, each base should build a tank if it has less than 5 tanks
            elif base.crystal > base.cost("tank") and self.ntanks[base.uid] < 10:
                # build_tank() returns the uid of the tank that was built
                tank_uid = base.build_tank(heading=360 * np.random.random())
                # Add 1 to the tank counter for this base
                self.ntanks[base.uid] += 1
            # Thirdly, each base should build a ship if it has less than 3 ships
            elif base.crystal > base.cost("ship") and self.nships[base.uid] < 3:
                # build_ship() returns the uid of the ship that was built
                ship_uid = base.build_ship(heading=360 * np.random.random())
                # Add 1 to the ship counter for this base
                self.nships[base.uid] += 1
            # If everything else is satisfied, build a jet
            elif base.crystal > base.cost("jet"):
                # build_jet() returns the uid of the jet that was built
                jet_uid = base.build_jet(heading=360 * np.random.random())

        # Try to find an enemy target
        enemy_bases = []
        for team_name in info:
            if team_name != self.team and "bases" in info[team_name]:
                enemy_bases.extend(info[team_name]["bases"])
        # print(f'{enemy_bases = }')

        # Controlling my vehicles ==============================================

        # Iterate through all my tanks
        if "tanks" in myinfo:
            for tank in myinfo["tanks"]:
                target = self.get_closest_base(tank, enemy_bases)
                if (tank.uid in self.previous_positions) and (not tank.stopped):
                    # If the tank position is the same as the previous position,
                    # set a random heading
                    if all(tank.position == self.previous_positions[tank.uid]):
                        tank.set_heading(np.random.random() * 360.0)
                    # Else, if there is a target, go to the target
                    elif target is not None:
                        # print(target.x, target.y)
                        tank.goto(target.x, target.y)
                # Store the previous position of this tank for the next time step
                self.previous_positions[tank.uid] = tank.position

        # Iterate through all my ships
        if "ships" in myinfo:
            for ship in myinfo["ships"]:
                if ship.uid in self.previous_positions:
                    # If the ship position is the same as the previous position,
                    # convert the ship to a base if it is far from the owning base,
                    # set a random heading otherwise
                    if all(ship.position == self.previous_positions[ship.uid]):

                        closest_base = self.get_closest_base(ship, myinfo["bases"])

                        if ship.get_distance(closest_base.x, closest_base.y) > COMPETING_MINE_RADIUS:
                            ship.convert_to_base()
                        else:
                            ship.set_heading(np.random.random() * 360.0)
                # Store the previous position of this ship for the next time step
                self.previous_positions[ship.uid] = ship.position

        # Iterate through all my jets
        if "jets" in myinfo:
            for jet in myinfo["jets"]:
                # Jets simply go to the target if there is one, they never get stuck
                target = self.get_closest_base(jet, enemy_bases)
                if target is not None:
                    jet.goto(target.x, target.y)
