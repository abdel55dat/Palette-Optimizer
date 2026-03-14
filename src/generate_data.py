import pandas as pd
import numpy as np
import random
import math

# Contraintes métier
MAX_PALETTES_SOL = 33
HAUTEUR_MAX_STACK_CM = 220

CLIENTS = ["MEDIA MARKT", "FNAC", "DARTY", "BOULANGER", "CDISCOUNT"]

DESTINATIONS = [
    {"ville": "Paris", "zip": "75001", "region": "IDF"},
    {"ville": "Lyon", "zip": "69001", "region": "ARA"},
    {"ville": "Marseille", "zip": "13001", "region": "PACA"},
    {"ville": "Bordeaux", "zip": "33000", "region": "NAQ"},
    {"ville": "Lille", "zip": "59000", "region": "HDF"},
]

TOURNEES_LTL = {
    "Tournée Nord": ["Lille"],
    "Tournée Sud": ["Marseille", "Bordeaux"],
    "Tournée Centre": ["Paris", "Lyon"],
}

SKUS = [
    {"sku": "EP2331/10", "description": "ESPRESSO MACHINE BLACK", "hauteur_cm": 32, "poids_kg": 4.5, "pack_config": 12},
    {"sku": "HD9137/90", "description": "AIR FRYER XL", "hauteur_cm": 38, "poids_kg": 6.2, "pack_config": 6},
    {"sku": "PSG8200/70", "description": "STEAM GENERATOR", "hauteur_cm": 45, "poids_kg": 3.8, "pack_config": 8},
    {"sku": "GC026/00", "description": "PILL REMOVER ACCESSORY", "hauteur_cm": 12, "poids_kg": 0.5, "pack_config": 48},
    {"sku": "STH5020/40", "description": "HANDHELD STEAMER RED", "hauteur_cm": 28, "poids_kg": 2.1, "pack_config": 20},
    {"sku": "LM9012/50", "description": "BARISTA COFFEEMAKER", "hauteur_cm": 42, "poids_kg": 8.3, "pack_config": 4},
    {"sku": "NA352/00", "description": "DUAL BAS CHAR GREY", "hauteur_cm": 35, "poids_kg": 5.0, "pack_config": 10},
    {"sku": "HR3741/00", "description": "MIXER VIVA CASHMERE", "hauteur_cm": 30, "poids_kg": 3.2, "pack_config": 15},
]


def generate_commandes(n_orders=20, seed=42):
    random.seed(seed)
    np.random.seed(seed)

    rows = []

    for order_idx in range(n_orders):
        order_id = 8005800000 + order_idx
        po_number = 190240000 + order_idx
        client = random.choice(CLIENTS)
        dest = random.choice(DESTINATIONS)
        stack_autorise = random.choice([True, False])
        delivery_date = "31/1/26"
        delivery_time = random.choice(["8:00", "12:00", "17:00", "21:00"])

        n_skus = random.randint(1, 4)
        for _ in range(n_skus):
            sku_info = random.choice(SKUS)
            pack_config = sku_info["pack_config"]

            # Quantité commandée — pas forcément un multiple du pack config
            qty = random.randint(1, pack_config * 3)

            # Calcul FP et LTL à partir du pack config
            nb_fp = qty // pack_config          # palettes complètes
            reste = qty % pack_config           # unités restantes → LTL

            rows.append({
                "ORDER_ID": order_id,
                "PO_NUMBER": po_number,
                "SKU": sku_info["sku"],
                "DESCRIPTION": sku_info["description"],
                "QTY_ORDERED": qty,
                "PACK_CONFIG": pack_config,
                "NB_FP": nb_fp,
                "QTY_LTL": reste,
                "HAS_LTL": reste > 0,
                "POIDS_KG": round(sku_info["poids_kg"] * qty, 2),
                "CUSTOMER": client,
                "ADDRESS": f"{random.randint(1, 50)} Rue de la Paix",
                "ZIP": dest["zip"],
                "TOWN": dest["ville"],
                "REGION": dest["region"],
                "HAUTEUR_PALETTE_CM": sku_info["hauteur_cm"],
                "STACK_AUTORISE": stack_autorise,
                "DELIVERY_DATE": delivery_date,
                "DELIVERY_TIME": delivery_time,
            })

    return pd.DataFrame(rows)


def generate_palettes(df_commandes):
    palettes = []
    pallet_counter = 1

    for _, row in df_commandes.iterrows():
        # Générer les FP
        for i in range(row["NB_FP"]):
            palettes.append({
                "PALLET_ID": f"PAL-{pallet_counter:04d}",
                "PALLET_TYPE": "FP",
                "ORDER_ID": row["ORDER_ID"],
                "SKU": row["SKU"],
                "QTY_SUR_PALETTE": row["PACK_CONFIG"],
                "CUSTOMER": row["CUSTOMER"],
                "TOWN": row["TOWN"],
                "REGION": row["REGION"],
                "ZIP": row["ZIP"],
                "HAUTEUR_PALETTE_CM": row["HAUTEUR_PALETTE_CM"],
                "POIDS_KG": round(row["POIDS_KG"] / (row["NB_FP"] + (1 if row["HAS_LTL"] else 0)), 2),
                "STACK_AUTORISE": row["STACK_AUTORISE"],
                "DELIVERY_DATE": row["DELIVERY_DATE"],
                "DELIVERY_TIME": row["DELIVERY_TIME"],
            })
            pallet_counter += 1

        # Générer la palette LTL si reste > 0
        if row["HAS_LTL"]:
            palettes.append({
                "PALLET_ID": f"PAL-{pallet_counter:04d}",
                "PALLET_TYPE": "LTL",
                "ORDER_ID": row["ORDER_ID"],
                "SKU": row["SKU"],
                "QTY_SUR_PALETTE": row["QTY_LTL"],
                "CUSTOMER": row["CUSTOMER"],
                "TOWN": row["TOWN"],
                "REGION": row["REGION"],
                "ZIP": row["ZIP"],
                "HAUTEUR_PALETTE_CM": row["HAUTEUR_PALETTE_CM"],
                "POIDS_KG": round(row["POIDS_KG"] * row["QTY_LTL"] / row["QTY_ORDERED"], 2),
                "STACK_AUTORISE": False,  # LTL jamais stacké
                "DELIVERY_DATE": row["DELIVERY_DATE"],
                "DELIVERY_TIME": row["DELIVERY_TIME"],
            })
            pallet_counter += 1

    return pd.DataFrame(palettes)


if __name__ == "__main__":
    df_cmd = generate_commandes(n_orders=20)
    df_pal = generate_palettes(df_cmd)

    print("COMMANDES")
    print(df_cmd[["ORDER_ID", "SKU", "QTY_ORDERED", "PACK_CONFIG", "NB_FP", "QTY_LTL", "TOWN"]].head(10))
    print(f"\nTotal FP : {df_cmd['NB_FP'].sum()} palettes")
    print(f"Total LTL : {df_cmd['HAS_LTL'].sum()} palettes partielles")
    print(f"\n=== PALETTES ===")
    print(df_pal[["PALLET_ID", "PALLET_TYPE", "SKU", "QTY_SUR_PALETTE", "TOWN"]].head(10))
    print(f"\nFP : {len(df_pal[df_pal['PALLET_TYPE']=='FP'])} palettes complètes")
    print(f"LTL : {len(df_pal[df_pal['PALLET_TYPE']=='LTL'])} lignes à consolider")
    print(f"Slots camion estimés : {len(df_pal[df_pal['PALLET_TYPE']=='FP'])} FP + palettes LTL consolidées")