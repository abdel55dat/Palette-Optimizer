import pandas as pd
from src.generate_data import MAX_PALETTES_SOL, HAUTEUR_MAX_STACK_CM


def optimiser_chargement(df_palettes):
    camions = []

    # Regrouper par destination ET client
    groupes = df_palettes.groupby(["TOWN", "CUSTOMER"])

    for (town, customer), group in groupes:
        df_fp = group[group["PALLET_TYPE"] == "FP"].to_dict("records")
        df_ltl = group[group["PALLET_TYPE"] == "LTL"].to_dict("records")

        ltl_restants = list(df_ltl)
        camion_actuel = None

        # Charger les FP en essayant de stacker les LTL dessus
        for fp in df_fp:
            hauteur_fp = fp["HAUTEUR_PALETTE_CM"]
            stack_autorise = fp["STACK_AUTORISE"]

            # Cherche une LTL compatible
            ltl_stackee = None
            if stack_autorise and ltl_restants:
                for ltl in ltl_restants:
                    if hauteur_fp + ltl["HAUTEUR_PALETTE_CM"] <= HAUTEUR_MAX_STACK_CM:
                        ltl_stackee = ltl
                        ltl_restants.remove(ltl)
                        break

            # Nouveau camion si nécessaire
            if camion_actuel is None or camion_actuel["slots_utilises"] + 1 > MAX_PALETTES_SOL:
                if camion_actuel:
                    camions.append(camion_actuel)
                camion_actuel = _nouveau_camion(len(camions) + 1, town, customer)

            slot = camion_actuel["slot_counter"]
            hauteur_totale = hauteur_fp + (ltl_stackee["HAUTEUR_PALETTE_CM"] if ltl_stackee else 0)

            camion_actuel["slots"][slot] = {
                "bottom": fp["PALLET_ID"],
                "top": ltl_stackee["PALLET_ID"] if ltl_stackee else None,
                "hauteur_totale_cm": hauteur_totale,
                "stacked": ltl_stackee is not None,
            }
            camion_actuel["palettes"].append(_palette_row(fp, slot, "BOTTOM"))
            if ltl_stackee:
                camion_actuel["palettes"].append(_palette_row(ltl_stackee, slot, "TOP"))

            camion_actuel["slots_utilises"] += 1
            camion_actuel["slot_counter"] += 1

        # LTL restantes non stackées → slots seuls
        for ltl in ltl_restants:
            if camion_actuel is None or camion_actuel["slots_utilises"] + 1 > MAX_PALETTES_SOL:
                if camion_actuel:
                    camions.append(camion_actuel)
                camion_actuel = _nouveau_camion(len(camions) + 1, town, customer)

            slot = camion_actuel["slot_counter"]
            camion_actuel["slots"][slot] = {
                "bottom": ltl["PALLET_ID"],
                "top": None,
                "hauteur_totale_cm": ltl["HAUTEUR_PALETTE_CM"],
                "stacked": False,
            }
            camion_actuel["palettes"].append(_palette_row(ltl, slot, "BOTTOM"))
            camion_actuel["slots_utilises"] += 1
            camion_actuel["slot_counter"] += 1

        if camion_actuel:
            camions.append(camion_actuel)

    # Renuméroter
    for i, c in enumerate(camions):
        c["id"] = i + 1

    return camions


def _nouveau_camion(id, destination, customer):
    return {
        "id": id,
        "destination_principale": destination,
        "customer": customer,
        "palettes": [],
        "slots": {},
        "slots_utilises": 0,
        "slot_counter": 1,
    }


def _palette_row(palette, slot, level):
    return {
        "PALLET_ID": palette["PALLET_ID"],
        "PALLET_TYPE": palette["PALLET_TYPE"],
        "ORDER_ID": palette["ORDER_ID"],
        "SLOT": slot,
        "LEVEL": level,
        "CUSTOMER": palette["CUSTOMER"],
        "TOWN": palette["TOWN"],
        "HAUTEUR_CM": palette["HAUTEUR_PALETTE_CM"],
    }


def resume_chargement(camions):
    rows = []
    for c in camions:
        nb_stacked = sum(1 for s in c["slots"].values() if s["stacked"])
        rows.append({
            "TRUCK_ID": f"Camion {c['id']}",
            "CLIENT": c["customer"],
            "DESTINATION": c["destination_principale"],
            "PALETTES_AU_SOL": c["slots_utilises"],
            "PALETTES_STACKEES": nb_stacked,
            "TAUX_REMPLISSAGE_%": round(c["slots_utilises"] / MAX_PALETTES_SOL * 100, 1),
            "NB_COMMANDES": len(set([p["ORDER_ID"] for p in c["palettes"]])),
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
                "STACKED": contenu["stacked"],
            })
    return pd.DataFrame(rows)


if __name__ == "__main__":
    from src.generate_data import generate_commandes, generate_palettes
    df_cmd = generate_commandes()
    df_pal = generate_palettes(df_cmd)
    camions = optimiser_chargement(df_pal)
    print("RÉSUMÉ")
    print(resume_chargement(camions).to_string())
    print("\nDÉTAIL CAMION 1")
    print(detail_chargement(camions)[:15].to_string())