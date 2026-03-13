import pandas as pd
from src.generate_data import MAX_PALETTES_SOL, HAUTEUR_MAX_STACK_CM


def optimiser_chargement(df_palettes):
    camions = []
    camion_actuel = {
        "id": 1,
        "palettes": [],
        "slots": {},  # slot -> [palette_bottom, palette_top?]
        "slot_counter": 1,
    }

    # Grouper les palettes par ORDER_ID pour ne pas splitter une commande
    orders = df_palettes.groupby("ORDER_ID")

    for order_id, group in orders:
        stack_autorise = group["STACK_AUTORISE"].iloc[0]
        hauteur = group["HAUTEUR_PALETTE_CM"].iloc[0]
        peut_stacker = stack_autorise and (hauteur * 2) <= HAUTEUR_MAX_STACK_CM
        palettes_order = group["PALLET_ID"].tolist()

        # Calcul des slots nécessaires pour cette commande
        if peut_stacker:
            slots_necessaires = -(-len(palettes_order) // 2)  # arrondi supérieur
        else:
            slots_necessaires = len(palettes_order)

        # Vérifie si la commande entière rentre dans le camion actuel
        slots_utilises = camion_actuel["slot_counter"] - 1
        if slots_utilises + slots_necessaires > MAX_PALETTES_SOL:
            # Camion plein, on en ouvre un nouveau
            camions.append(camion_actuel)
            camion_actuel = {
                "id": len(camions) + 1,
                "palettes": [],
                "slots": {},
                "slot_counter": 1,
            }

        # Chargement des palettes dans le camion
        palette_iter = iter(palettes_order)
        for palette_id in palette_iter:
            slot = camion_actuel["slot_counter"]
            if peut_stacker:
                # On essaie de mettre 2 palettes par slot
                try:
                    palette_top = next(palette_iter)
                    camion_actuel["slots"][slot] = {
                        "bottom": palette_id,
                        "top": palette_top,
                        "hauteur_totale_cm": hauteur * 2,
                    }
                except StopIteration:
                    # Nombre impair, dernière palette seule
                    camion_actuel["slots"][slot] = {
                        "bottom": palette_id,
                        "top": None,
                        "hauteur_totale_cm": hauteur,
                    }
            else:
                camion_actuel["slots"][slot] = {
                    "bottom": palette_id,
                    "top": None,
                    "hauteur_totale_cm": hauteur,
                }
            camion_actuel["palettes"].append({
                "PALLET_ID": palette_id,
                "ORDER_ID": order_id,
                "SLOT": slot,
                "LEVEL": "BOTTOM",
                "HAUTEUR_CM": hauteur,
                "STACK_AUTORISE": stack_autorise,
                "CUSTOMER": group["CUSTOMER"].iloc[0],
                "TOWN": group["TOWN"].iloc[0],
            })
            camion_actuel["slot_counter"] += 1

    camions.append(camion_actuel)
    return camions


def resume_chargement(camions):
    rows = []
    for c in camions:
        slots_utilises = c["slot_counter"] - 1
        clients = list(set([p["CUSTOMER"] for p in c["palettes"]]))
        villes = list(set([p["TOWN"] for p in c["palettes"]]))
        rows.append({
            "TRUCK_ID": f"Camion {c['id']}",
            "PALETTES_AU_SOL": slots_utilises,
            "TAUX_REMPLISSAGE_%": round(slots_utilises / MAX_PALETTES_SOL * 100, 1),
            "NB_COMMANDES": len(set([p["ORDER_ID"] for p in c["palettes"]])),
            "CLIENTS": ", ".join(clients),
            "DESTINATIONS": ", ".join(villes),
        })
    return pd.DataFrame(rows)


def detail_chargement(camions):
    rows = []
    for c in camions:
        for slot, contenu in c["slots"].items():
            rows.append({
                "TRUCK_ID": c["id"],
                "SLOT": slot,
                "PALLET_BOTTOM": contenu["bottom"],
                "PALLET_TOP": contenu["top"] if contenu["top"] else "-",
                "HAUTEUR_TOTALE_CM": contenu["hauteur_totale_cm"],
                "STACKED": contenu["top"] is not None,
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from src.generate_data import generate_commandes, generate_palettes
    df_cmd = generate_commandes()
    df_pal = generate_palettes(df_cmd)
    camions = optimiser_chargement(df_pal)
    print("RÉSUMÉ")
    print(resume_chargement(camions))
    print("\nDÉTAIL CAMION 1")
    print(detail_chargement(camions)[:10])