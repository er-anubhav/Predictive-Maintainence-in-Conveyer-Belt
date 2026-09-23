import sys
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from sqlalchemy import select
from app.core.database import SessionLocal, engine
from app.models.mine import Mine
from app.models.conveyor import Conveyor
from app.models.sensor_node import SensorNode


def seed_database():
    print("🌱 Seeding development database...")
    db = SessionLocal()
    try:
        # 1. Seed Mine
        mine = db.execute(select(Mine).where(Mine.name == "Demo Iron Ore Mine")).scalar_one_or_none()
        if not mine:
            mine = Mine(
                name="Demo Iron Ore Mine",
                location="Odisha Sector 4, Mining Block B",
            )
            db.add(mine)
            db.commit()
            db.refresh(mine)
            print(f"  [+] Created Mine: {mine.name} (ID: {mine.id})")
        else:
            print(f"  [~] Mine already exists: {mine.name} (ID: {mine.id})")

        # 2. Seed Conveyor
        conveyor = db.execute(
            select(Conveyor).where(Conveyor.name == "Conveyor-01", Conveyor.mine_id == mine.id)
        ).scalar_one_or_none()

        if not conveyor:
            conveyor = Conveyor(
                mine_id=mine.id,
                name="Conveyor-01",
                belt_type="Steel Cord",
                length=100.0,
                width=1.2,
                status="OPERATIONAL",
            )
            db.add(conveyor)
            db.commit()
            db.refresh(conveyor)
            print(f"  [+] Created Conveyor: {conveyor.name} (ID: {conveyor.id})")
        else:
            print(f"  [~] Conveyor already exists: {conveyor.name} (ID: {conveyor.id})")

        # 3. Seed Sensor Nodes
        nodes_to_seed = [
            {
                "node_code": "NODE-001",
                "location": "Head Drive Pulley & Discharge Zone",
                "firmware_version": "v1.0.0",
                "status": "ONLINE",
            },
            {
                "node_code": "NODE-002",
                "location": "Tail Pulley & Loading Skirt Zone",
                "firmware_version": "v1.0.0",
                "status": "ONLINE",
            },
        ]

        for node_info in nodes_to_seed:
            existing_node = db.execute(
                select(SensorNode).where(SensorNode.node_code == node_info["node_code"])
            ).scalar_one_or_none()

            if not existing_node:
                node = SensorNode(
                    conveyor_id=conveyor.id,
                    node_code=node_info["node_code"],
                    location=node_info["location"],
                    firmware_version=node_info["firmware_version"],
                    status=node_info["status"],
                )
                db.add(node)
                db.commit()
                db.refresh(node)
                print(f"  [+] Created Sensor Node: {node.node_code} at {node.location} (ID: {node.id})")
            else:
                print(f"  [~] Sensor Node already exists: {existing_node.node_code} (ID: {existing_node.id})")

        print("✅ Seeding completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"❌ Error during seeding: {e}", file=sys.stderr)
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
