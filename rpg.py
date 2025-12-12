import time
import random
import datetime
import json

class Character:
    def __init__(self, name, health, damage):
        self.name = name
        self.health = health
        self.damage = damage

    def attack(self, target):
        min_dmg = self.damage - 3
        max_dmg = self.damage + 3

        actual_damage = random.randint(min_dmg, max_dmg)

        target.health -= actual_damage

        if target.health < 0:
            target.health = 0

        print(f"⚔️ {self.name} ударил {target.name} на {actual_damage} урона! (Разброс: {min_dmg}-{max_dmg})")
        print(f"   У {target.name} осталось {target.health} HP")

class Player(Character):
    def __init__(self, name, health, damage):
        super().__init__(name, health, damage)

class Enemy(Character):
    def __init__(self, name, health, damage):
        super().__init__(name, health, damage)

hero = Player(name="Викинг", health=100, damage=12)
trol = Enemy(name="Троль", health=100, damage=8)

input("Нажми Enter, чтобы начать битву с Троллем! 🛡️")

while hero.health > 0 and trol.health > 0:
    print("\n--------------------")

    hero.attack(trol)

    if trol.health <= 0:
        print(f"\n💀 {trol.name} повержен!")
        break

    time.sleep(1)

    trol.attack(hero)

    if hero.health <= 0:
        print(f"\n💀 {hero.name} повержен!")
        break

    time.sleep(1)

print("\n=== Битва окончена ===")
if hero.health > 0:
    print(f"🎉 {hero.name} победил и забирает золото!")
else:
    print("🪦 Герой пал в бою... Game Over.")

now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

winner_name = hero.name if hero.health > 0 else trol.name


battle_data = {
    "time": now,
    "player": hero.name,
    "enemy_name": trol.name,
    "winner": winner_name,
    "health": hero.health,
}

with open(".venv/battle_result.json", "w", encoding="utf-8") as file:
    json.dump(battle_data, file, ensure_ascii=False, indent=4)

with open(".venv/battle_log.txt", "a", encoding="utf-8") as file:
    if hero.health > 0:
        file.write(f"[{now}] Победа! Викинг одолел Тролля.\n")
    else:
        file.write(f"[{now}] Поражение... Викинг пал.\n")

print("Результат записан в battle_log.txt")


