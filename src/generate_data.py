import pandas as pd
import numpy as np
import random

# Contraintes métier
MAX_PALETTES_SOL = 33
HAUTEUR_MAX_STACK_CM = 220  # en cm

# Données de référence fictives
CLIENTS = ["MEDIA MARKT", "FNAC", "DARTY", "BOULANGER", "CDISCOUNT"]

VILLES = [
    {"ville": "Paris", "zip": "75001"},
    {"ville": "Lyon", "zip": "69001"},
    {"ville": "Marseille", "zip": "13001"},
    {"ville": "Bordeaux", "zip": "33000"},
    {"ville": "Lille", "zip": "59000"},
]

SKUS = [
    {"sku": "EP2331/10", "description": "ESPRESSO MACHINE BLACK", "hauteur_cm": 32},
    {"sku": "HD9137/90", "description": "AIR FRYER XL", "hauteur_cm": 38},
    {"sku": "PSG8200/70", "description": "STEAM GENERATOR GREEN", "hauteur_cm": 45},
    {"sku": "GC026/00", "description": "PILL REMOVER ACCESSORY", "hauteur_cm": 12},
    {"sku": "STH5020/40", "description": "HANDHELD STEAMER RED", "hauteur_cm": 28},
    {"sku": "LM9012/50", "description": "BARISTA COFFEEMAKER", "hauteur_cm": 42},
    {"sku": "NA352/00", "description": "DUAL BAS CHAR GREY", "hauteur_cm": 35},
    {"sku": "HR3741/00", "description": "MIXER VIVA CASHMERE", "hauteur_cm": 30},
]

def generate_commandes(n_orders=100, seed=42):
    random.seed(seed)
    np.random.seed(seed)

    rows = []
    pallet_id_counter = 1

    for order_idx in range(n_orders):
        order_id = 8005800000 + order_idx
        po_number = 190240000 + order_idx
        client = random.choice(CLIENTS)
        ville_info = random.choice(VILLES)
        stack_autorise = random.choice([True, False])
        delivery_date = "31/1/26"
        delivery_time = random.choice(["8:00", "12:00", "17:00", "21:00"])

        # Chaque commande a plusieurs lignes SKU
        n_skus = random.randint(1, 4)
        for _ in range(n_skus):
            sku_info = random.choice(SKUS)
            qty = random.randint(1, 10)
            volume = round(random.uniform(0.5, 7.5), 2)
            weight = round(random.uniform(50, 1500), 2)
            layers = random.randint(1, 2) if stack_autorise else 1

            rows.append({
                "ORDER_ID": order_id,
                "PO_NUMBER": po_number,
                "SKU": sku_info["sku"],
                "DESCRIPTION": sku_info["description"],
                "QTY_ORDERED": qty,
                "CUSTOMER": client,
                "ADDRESS": f"{random.randint(1,50)} Rue de la Paix",
                "ZIP": ville_info["zip"],
                "TOWN": ville_info["ville"],
                "VOLUME": volume,
                "WEIGHT": weight,
                "HAUTEUR_PALETTE_CM": sku_info["hauteur_cm"],
                "STACK_AUTORISE": stack_autorise,
                "LAYERS_ALLOWED": layers,
                "DELIVERY_DATE": delivery_date,
                "DELIVERY_TIME": delivery_time,
            })

    return pd.DataFrame(rows)


def generate_palettes(df_commandes):
    """Transforme les lignes de commande en palettes physiques"""
    palettes = []
    pallet_counter = 1

    for order_id, group in df_commandes.groupby("ORDER_ID"):
        stack_autorise = group["STACK_AUTORISE"].iloc[0]
        hauteur = group["HAUTEUR_PALETTE_CM"].iloc[0]
        client = group["CUSTOMER"].iloc[0]
        ville = group["TOWN"].iloc[0]
        delivery_date = group["DELIVERY_DATE"].iloc[0]
        delivery_time = group["DELIVERY_TIME"].iloc[0]

        # Une palette par ligne SKU
        for _, row in group.iterrows():
            palettes.append({
                "PALLET_ID": f"PAL-{pallet_counter:04d}",
                "ORDER_ID": order_id,
                "SKU": row["SKU"],
                "CUSTOMER": client,
                "TOWN": ville,
                "ZIP": row["ZIP"],
                "HAUTEUR_PALETTE_CM": hauteur,
                "STACK_AUTORISE": stack_autorise,
                "DELIVERY_DATE": delivery_date,
                "DELIVERY_TIME": delivery_time,
            })
            pallet_counter += 1

    return pd.DataFrame(palettes)


if __name__ == "__main__":
    df_cmd = generate_commandes()
    df_pal = generate_palettes(df_cmd)
    print("=== COMMANDES ===")
    print(df_cmd.head(5))
    print(f"\nTotal lignes commandes : {len(df_cmd)}")
    print(f"\n=== PALETTES ===")
    print(df_pal.head(5))
    print(f"\nTotal palettes : {len(df_pal)}")