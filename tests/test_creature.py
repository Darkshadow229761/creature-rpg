import unittest

from game import Creature


class CreatureTests(unittest.TestCase):
    def test_creature_starts_at_max_hp(self):
        creature = Creature("Test Pet", max_hp=30, attack=8, defense=2)
        self.assertEqual(creature.hp, 30)

    def test_damage_reduces_hp_without_going_below_zero(self):
        creature = Creature("Test Pet", max_hp=10, attack=8, defense=0)
        creature.hp = 3

        creature.take_damage(100)

        self.assertEqual(creature.hp, 0)
        self.assertTrue(creature.fainted)


if __name__ == "__main__":
    unittest.main()
