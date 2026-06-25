#!/usr/bin/env python3
"""Seed all DriveNets employees into the multi-user topology database.

Usage:
    python3 seed_users.py              # seed all ~640 employees (legacy name-derived)
    python3 seed_users.py --dry-run    # show what would be created
    python3 seed_users.py --list       # print username/password table
    python3 seed_users.py --csv FILE   # import from CSV (firstname,lastname,role)
    python3 seed_users.py --from-email-cache PATH   # seed from email-resolver cache

The ``--from-email-cache`` mode is the modern path: it consumes the JSON
written by ``api.migrations.email_resolver`` and uses the verified
``@drivenets.com`` email local part as the username. This guarantees
that a fresh deployment has the *same* usernames the existing
production DB will end up with after the username migration runs, so
new and migrated environments stay identity-compatible.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from api.auth.identity import (
    InvalidIdentityError,
    derive_username_from_email,
    is_company_email,
)
from api.auth.user_store import user_store

# Operator-controlled rollout password. Every new user seeded after the
# username -> email-local-part rename gets this; existing users are
# brought to parity by ``api.migrations.reset_passwords``. Both code
# paths share the same constant so a fresh deployment and a migrated
# one are credential-compatible. Override per-invocation with
# ``--password`` (or pass ``--legacy-password`` to fall back to the old
# sanitised-last-name convention).
UNIFIED_DEFAULT_PASSWORD = "drive1234"

ROLE_OVERRIDES: Dict[str, str] = {
    "Yarel Or": "admin",
    "Tal Shevach": "team_leader",
    "Galit Gabay": "team_leader",
    "Ohad Dahan": "team_leader",
    "Constantin Ilinca": "team_leader",
}

EMPLOYEES_RAW = """Abishek SureshKumar, Adi Karolitsky, Adi Offer, Adrian Caulea, Adrian Iavorschi, Adrian Partenie, Adrian Popescu, Agam Levi, Aleksandr Itkin, Alex Gelberger, Alex Gotlib, Alex Itkin, Alex Shundrin, Alex Zilberman, Alexander (Sasha) Barshay, Alexandru Costake, Alexandru Frujina, Alexandru Modiga, Alexandru Onofrei, Alexandru Spinu, Alexandru Stere, Alin Rauta, Alina Berestetsky, Alina Dalcu, Almog Ashkenazi, Almog Mesilaty, Alon Bar-Esh, Alon Maor, Alvin Yu Zhang, Amir Barak, Amir Ben avraham, Amir Bloch, Amir Eshel, Amir Foox, Amir Krayden, Amir Kurnaz, Amir Rachum, Amir Tsvitov, Amir Zimmerman, Amit Chai, Amit Cohen, Amit Gabay, Amit Gilad, Amit Goren, Amit Hazan, Amit Maoz, Amit Weiss, Amol Junghare, Ana-Maria Manolache, Anat Ran, Andreea Fundeanu, Andreea Gheorghisan, Andrei Buia, Andrei Gheorghiu, Andrei Lazar, Andrei Manzicu, Andrei Nicoara, Andrei Roba, Andrei Simion, Andrei Stancu, Andrei Vieru, Andrew Holland, Andrey Mavlyanov, Ankur Parashar, Anna Kukuy, Anna Uzdensky, Anna Yefimov, Anya Levin, Arad Zilberberg, Arie Ron, Arie Rozentul, Ariel Chinn, Ariel Kdoshay, Arik Caspi, Arik Gelman, Armand - Adrian Moldoveanu, Artur Yablotski, Arye Shalev, Asaf Barda, Asaf Baron, Asaf Jerbi, Asaf Mesika, Asaf Shiloah, Assaf Cwajghaft, Assaf Peer, Atai Natan, Atsushi Shimazaki, Attila Magyari, Avi Eframov, Aviraz Mordechai, Aviv Ashkelon, Bar Moskovich, Bar Omri, Bar Sidon, Bar Zrihan, Barak Vanunu, Baruch Atzmon, Becky Uzdensky, Ben Posnasky, Ben Saacks, Benda, Bogdan Blidarescu, Bogdan Istoc, Borislav Glozman, Bradley Riapolov, Calin Miculescu, Catalin Mateiu, Catalin Pacurariu, Catalina Rosu, Chandra Gonuguntla, Chen Bary, Chen Goldenberg, Chen Koifman, Chen Oz, Chengsheng Luo, Chuck Johnson, Ciprian Fuge, Ciprian Marmureanu, Claudiu Boriga, Constantin Ilinca, Constantine Abramovich, Cosmin Grigoruta, Cristian Chiriac, Cristian Dorobat, Cristian Liviu Iosif Pop, Cristian Pantea, Cristian-Alexandru Olaru, Cristiana Elena Nehoianu, Dalit Levi, Dan Rosu, Dan Shelef, Dan Voiculeasa, Dana Gubarev, Dana Shemesh, Dani Kaganovitch, Daniel Badea, Daniel Dragomirescu, Daniel Lande, Daniel Lion, Daniel Litvinenko, Daniel Niculescu, Daniel Oren, Daniel Roytenberg, Daniel Shachrur, Daniel Stroikin, Daniel Tal, Daniel Varshavski, Daniel Yonayov, Daniel Zhuchenko, Daniela Rampani, Danna Boiko, Daria Dekova, Darlene Corrubia, Dat Ngo, David Brooks, David Shuva, David Sung, David Watson, Dganit Gozali Gottesman, Diana Mevorach, Diana Vexler, Dimitry Raitses, dknight, Dmitry Bas, Dmitry Kravkov, Dmitry Zvernik, Dor Kaiser, Doron Darmoni, Dov Libermensh, Dovev Peleg, Dragos Lazar, Dragos Marinescu, Dragos Nicolaescu, Dragos Stroe, Dudi Brooks, Dudy Cohen, Eden Dayan, Eden Haelyon, Eden Hassid, Eden Shilo, Edo Talmor, Eduard Haimov, Efi Talor, Ehud Asraf, Eitan Ben-Ari, Elad Ben Ezra, Elad Binyamin, Elad Sasson, Elad Zaltsman, EladCo, Elay Marzuk, Elena Mang, Eli Gabbay, Eli Moskovitch, Eliezer Kosharovsky, Eliezer Razon, Eliyahu Bollack, Emilian Filipescu, Engin Zeren, Eran Ariav, Eran Ben Eli, Eran Hendler, Eran Tzabari, Erez Fremder, Esther Beyda, Evgeny Hershkovitch Neiterman, Evyatar Daud, Eyad Gomid, Eyal Harel, Eyal Hezi, Eyal Horn, Eyal Kazula, Felix Weinstein, Firas Ighbaria, Flavia Pop, Florin Marius Popescu, Florin Popescu, Florin Rosulescu, Gabriel Iulian Serghei, Gabriel Tanase, Gadi Elizur, Gadi Kaplan, Gal Bar, Galit Gabay, Gary Brennan, Gemini, Gennady Mescheryakov, George Balint, Georgiana Girlea, Gidron Bloch, Gigi Gheorghiceanu, Gil Ben Basat, Gil Gisis, Gil Granot, Gil Nudelman, Gila Zadok, Gilad Maya, Gilad Meirovich, Gili Shiller Bider, Gili Stein Moreno, Gisel Rotenberg, Gonen Cohen, Gregory Freilikhman, Guy Baskind, Guy Harmelin, Guy Katz, Guy Shafir, Guy Stern, Gvir Sharon, Hadar Bater Idan, Hadar Bublil, Hadar Harari, Hagai Sela, Hagit Badash, Hai Balas, Hai Swissa, Hanna Ben-Moshe, Hannah Mordechai, Hanoch Yarkoni, Harel Manheim, Harel Turgeman, Hen Haklai, Hezi Eini, Hideya Kaneko, Hila Nachshon, Hillel Kobrinsky, Idan Grave, Idan Matityahu, Idit Eden, Idit Yoskovitz, Ido Ben Ami, Ido Hai, Ido Karmi, Ido Koren, Ido Lev-ran, Ido Schwartz, Ido Shenbach, Ido Susan, Idris Jafarov, Igor Vigasin, Ilana Staretz-Arie, Iliya Zaidman, Ilya Khlyap, Ilya Levin, Inbal Matityahu, Inbar Lasser-raab, Inon Lahyany, Ioana Staicu, Ion Sirbu, Ion-Lucian Marinescu, Ionel Calinescu, Ionut Alexa, Isaac Elbaz, Israel Galkin, Itamar Brem, Itamar Katz, Itay Lugasi, Itzik Moshaof, Itzik Tzruya, Iulia Tanasescu, Iustin Dumitrescu, Jade Mansour, Jesse Schlegel, Juan Rodriguez Martinez, Judith Sirotsky, Julia Perlits Aharon, Kacper Borucki, Karin Forkosh, Karina Shalmiev, Katie Evseev, Katya Dolgov, Kaylan Kreizer, Keren Blesser, Keren Dadon, Keren Litvak, Kezie Iwueke, Kira Mironov, Kumaran Gopalan, Lahav Schlesinger, Lavie Gariv, Lea Gutin, Lee Uziel, Leonardo van Schaik, Leonid Berman, Libin Varghese, Lidor Volinsky, Lidor Zino, Lilac Eilim, Lior Ashkenazi, Lior Basil, Lior Peles, Lior Plat, Lior Rubin, Lisa Zhao, Lucian Ciobanu, Maayan Jacobowitz, Maisharel Davidson, Makoto Onuma, Malkiel Bellaish, Marco Supino, Marian Adam, Marius Chelu, Marius Ionescu, Marius Miu, Marius Supuran, Martin Perlin, Masaki Moriwaki, Masami Takebayashi, Masao Inouye, Masaru Akai, Matan Azizi, Matan Entin, Matei Negriu, Matias Semrik, Matthew Zhivaev, Max Shestakov, Maxim Ivaschetsky, Maya Iwanir, Maya Peri, Meidan Rubin, Menachem Dodge, Merav Eytan, Michael Budiyashin, Michael Chernitsky, Michael Gonen, Michael Plotkin, Michael Seletsky, Michael Shapiro, Michal Allon Zitiat, Michal Ifrach, Michal Segal, Mihaela Maracine, Mihai Cacior, Mihai Ochiu, Mikael Chamalet, Mike Erlihson, Mircea Barbu, Mircea-George Zavate, Moawiya Haj Yahia, Mohamed Ashiq Ali, Mohammed Rameez Bappathimandakath, Mor Shlomi, Moran Ressler Arazi, Moshe Belfer, Moshe Elbaz, Moshe Shemesh, Moti Schreiber, Naama Elberg, Naama Ofek Arad, Nachum Eibschutz, Nadav Cohen, Nadav Kehati, Naor Chuosho, Natan Shabtayev, Neria Uzan, Netanel Levi, Nicolae Alexandrescu, Nik Lerman, Nikita Goldvarg, Nikita Kiosse, Nir Aroeti, Nir Ben David, Nir Fux, Nir Gasko, Nir Michael, Nir Shaknay, Nir Zoref, Nitsan Stoler, Nitzan Ben Shahar, Niv Bromberg, Niv Shcherb, Niv Tobias, Noa Halaly, Noa Mozes, Noa Volk, Noam Hadar, Noam Peleg, Nofar Keinan, Noga Abramovitch, Noga Henchinski, Noga Morag, Nokki Choeynim, Noor Khamaisy, Noy Zukrel, Oded Engel, Oded Hassidi, Ofek Alfasi, Ofek Tal, Ofer Ben Zvi, Ofer Schreiber, Ohad Dahan, Ohad Zvi Shaboo, Omer Dahan, Omer Tati, Omri Asulin, Omri Glass, Omri Litvak, Omri Nir, Omri Peri, Omri Sagiv, Ophir Arbiv, Ophir de Jager, Orel Balilti, Oren Asass, Ori Isachar, Ori Moisis, Ori Monrov, Ori Nagar, Ori Zeiri, Orit Shenhav Meltzer, Ovidiu Angheluta, Ovidiu Poncea, Ovidiu Simion, Pankaj Kumar, Paul Robu, Pavel Komissar, Pavel Rosenboim, Phillip Chang, Quanrui Ge, Rachel Shiloh, Radu Ghita, Rafi Gabzu, Rahul Nema, Rajesh Thukaram, Raluca Serban, Ramesh Putta, Ran Proshan, Randal Cevallos, Rani Finkelstein, Ravali Samineni, Ravid Goldenberg, Raz Amir, Razvan Serbanescu, Regev Eyal, Regev Nir, Renana Turgeman, Reuven Buber, Richard Henderson, Rina Berlin, Rina Reiman, Roee Sadeh, Roi Becker, Roi Dayan, Roi Shabi, Ron Gorlovsky, Ron Shmulinson, Ronen Mymon, Ronen Varfman, Roni Braunstein, Roni Goldenberg, Rotem Kfir, Roy Keisi, Roy Lamdan, Roy Vazana, Rupa Chatterjee, Sabin Deaconu, Sagie Fanish, Sagit Kadmon, Sandeep Bundela, Sani Ronen, Satoshi Okano, Sefi Frieman, Shachar Abramson, Shachar Alfia, Shahar Dov, Shahar Fermon, Shahar Gamliel, Shahar Levi, Shahar Maron, Shai Haim, Shai Peretz, Shai Zilber, Shaked Abdu, Shaked Matar, Shani Geula, Sharon Goren, Sharon Oren, Shashang Shah, Shay (Yehoshua) Israel, Shay Kulnevsky, Shelly Golden, Shimon Eytan, Shimon Mordooch, Shimrit Melamed, Shir Reifenberg, Shiran Aizik, Shiran Dapht, Shiran Shemesh, Shlomi Vainberger, Shmulik Atia, Shon Avri, Shoshana Huri, Shuli Paz, Shunsuke Sasaki, Sigal Amano, Simcha Wolfson, Slava Isaev, Snir Maduel, Stefan Bradulet, Stefan Dinescu, Stefan Vasilache, Stelian Slave, Sunanda Veganti, Sunil Mayenkar, Tal Bar, Tal Benjo, Tal Gaon, Tal Goldman, Tal Mussayoff, Tal Shevach, Tal Tavor-grinberg, Tal Tzadka, Tali Itzhar, Tamara David, Tamir Gal, Tammi Leibovitch, Tatsuyoshi Semboku, Tian Yeong Lim, Tilak Raj, Tom Aviv, Tom Bar-Hay, Tom Mor, Tom Ronen, Tom Yamini, Tomer Babamuratov, Tomer Lotan, Tomer Mevorach, Tomer Wellingstein, Tzvika Naveh, Uri Bar-Frank, Uri Odem, Uriel Sirota, Valentin Balan, Vasant Narayanan, Vasile Floroiu, Vasily Kluchnikov, VAX, Vicki Donchenko, Victor Gabriel Costin, Victor Zhuhovitsky, Viktor Cherviakov, Vilian Postovaru, Virgiliu Pop, Vishal Katkar, Vitaly Belman, Vitaly Lebedev, Vivek Gupta, Vlad Doros, Vlad Paninopol, Vladi Polonsky, Vladimir Shvidler, Vladislav Romanov, Vova Katz, Vova Svidinsky, Yahav Jakubowicz avraham, Yair Muschinsky, Yakir Hadad, Yanal Tehaucha, Yaniv Kleinman, Yaniv Lichter, Yaniv Taieb, Yanni Vandenbossche, Yarel Or, Yarin Hanania, Yaron Yechieli, Yaroslav (Ice) Sheremet, Yasmin Irshied, Yatin Lokhande, Yechiel babani, Yehonatan Ailon, Yevgeniy Petrochuk, Yinat Namir-Trompoler, Yinon Elkabetz, Yoav Spector, Yohay Artzi, Yonatan Ariel, Yonatan Chekol, Yonatan Cohen, Yonatan Linik, Yonatan Mateh, Yosefa Shulman, Yosi Zilberberg, Yossi Ben Eytan, Yossi Kikozashvili, Yossi Mozgerashvily, Yotam Kalmanovitz, Yuri Grigorian, Yuval Eshed Buzaglo, Yuval Haimovitch, Yuval Lerman, Yuval Tendler, Zachary Berrih, Zamir Paltiel, Zevi Grunbaum, Zion Tegenia, Ziv Gissis, Zohar Belkin, Zohar Keiserman"""


def _parse_name(full_name: str) -> Tuple[str, str]:
    """Split 'First Last' into (first, last). Handles multi-word last names."""
    full_name = full_name.strip()
    # Strip parenthetical nicknames: "Shay (Yehoshua) Israel" -> "Shay Israel"
    full_name = re.sub(r"\s*\([^)]*\)\s*", " ", full_name).strip()
    # "Armand - Adrian Moldoveanu" -> "Armand-Adrian Moldoveanu"
    full_name = re.sub(r"\s*-\s*", "-", full_name)

    parts = full_name.split()
    if len(parts) == 1:
        return parts[0].lower(), parts[0].lower()
    first = parts[0].lower()
    last = "".join(p.lower() for p in parts[1:])
    # Remove hyphens from password but keep in username for readability
    return first, re.sub(r"[^a-z0-9]", "", last)


def _sanitize_username(name: str) -> str:
    """Make a string safe for use as username: lowercase alphanumeric + dots + hyphens."""
    return re.sub(r"[^a-z0-9.\-]", "", name.lower())


def generate_user_list(raw: str) -> List[Dict[str, str]]:
    """Parse raw comma-separated names and generate unique usernames."""
    names = [n.strip() for n in raw.split(",") if n.strip()]
    entries: List[Tuple[str, str, str]] = []
    for name in names:
        first, last = _parse_name(name)
        entries.append((name, first, last))

    first_counts = Counter(first for _, first, _ in entries)

    users = []
    seen_usernames: set = set()
    for display_name, first, last in entries:
        first_clean = _sanitize_username(first)
        last_clean = _sanitize_username(last)
        if not first_clean or not last_clean:
            continue

        if first_counts[first] == 1:
            username = first_clean
        else:
            username = f"{first_clean}.{last_clean}"

        # Deduplicate (in case of identical full usernames)
        base = username
        counter = 2
        while username in seen_usernames:
            username = f"{base}{counter}"
            counter += 1
        seen_usernames.add(username)

        role = ROLE_OVERRIDES.get(display_name, "engineer")
        password = last_clean if len(last_clean) >= 2 else last_clean + "123"

        users.append({
            "display_name": display_name,
            "username": username,
            "password": password,
            "role": role,
        })
    return users


def seed_all(dry_run: bool = False, show_list: bool = False):
    users = generate_user_list(EMPLOYEES_RAW)
    print(f"[INFO] Generated {len(users)} users from employee list")

    if show_list:
        print(f"\n{'Username':<30} {'Password':<25} {'Role':<14} {'Display Name'}")
        print("-" * 100)
        for u in users:
            print(f"{u['username']:<30} {u['password']:<25} {u['role']:<14} {u['display_name']}")
        return

    created = 0
    skipped = 0
    errors = 0
    for u in users:
        if dry_run:
            existing = user_store.get_user(u["username"])
            status = "SKIP (exists)" if existing else "CREATE"
            print(f"  [{status}] {u['username']} ({u['role']}) - {u['display_name']}")
            if not existing:
                created += 1
            else:
                skipped += 1
            continue

        existing = user_store.get_user(u["username"])
        if existing:
            skipped += 1
            continue
        try:
            user_store.create_user(
                username=u["username"],
                password=u["password"],
                display_name=u["display_name"],
                role=u["role"],
            )
            created += 1
            print(f"  [OK] Created {u['username']} ({u['role']})")
        except Exception as e:
            errors += 1
            print(f"  [ERROR] {u['username']}: {e}")

    print(f"\n[DONE] Created: {created}, Skipped: {skipped}, Errors: {errors}")


def seed_from_csv(csv_path: str, dry_run: bool = False):
    """Import users from CSV: firstname,lastname,role (optional)"""
    users = []
    with open(csv_path) as f:
        reader = csv.reader(f)
        for row in reader:
            if len(row) < 2:
                continue
            first = row[0].strip().lower()
            last = row[1].strip().lower()
            role = row[2].strip() if len(row) > 2 else "engineer"
            display_name = f"{row[0].strip()} {row[1].strip()}"
            username = f"{first}.{last}" if first and last else first
            password = re.sub(r"[^a-z0-9]", "", last) or "changeme"
            users.append({
                "display_name": display_name,
                "username": _sanitize_username(username),
                "password": password,
                "role": role,
            })

    print(f"[INFO] Parsed {len(users)} users from {csv_path}")
    for u in users:
        if dry_run:
            print(f"  [DRY-RUN] {u['username']} ({u['role']})")
            continue
        existing = user_store.get_user(u["username"])
        if existing:
            print(f"  [SKIP] {u['username']} already exists")
            continue
        try:
            user_store.create_user(
                username=u["username"],
                password=u["password"],
                display_name=u["display_name"],
                role=u["role"],
            )
            print(f"  [OK] Created {u['username']}")
        except Exception as e:
            print(f"  [ERROR] {u['username']}: {e}")


def _password_for(display_name: str, fallback_username: str) -> str:
    """Pick a deterministic, low-friction first-login password.

    Mirrors the legacy convention (sanitized last name, fall back to the
    sanitized full name, then to the username + ``123``). Operators are
    expected to force users through password change on first login --
    this is the same posture we have today.
    """
    name = display_name or fallback_username
    name = re.sub(r"\s*\([^)]*\)\s*", " ", name).strip()
    parts = [p for p in re.split(r"\s+", name) if p]
    if not parts:
        return f"{fallback_username}123"
    last = parts[-1] if len(parts) > 1 else parts[0]
    last = re.sub(r"[^a-z0-9]", "", last.lower())
    if len(last) >= 2:
        return last
    return f"{fallback_username}123" if fallback_username else f"{last}123"


def _load_email_cache(path: Path) -> Dict[str, Dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Email cache not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"Email cache {path} is not valid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"Email cache {path} must be a JSON object at top level")
    return data


def seed_from_email_cache(
    cache_path: Path,
    *,
    dry_run: bool = False,
    include_inactive: bool = False,
    password: Optional[str] = None,
    use_legacy_password: bool = False,
) -> None:
    """Seed users using the email resolver's cache as the source of truth.

    Each cache entry must have ``status == "matched"`` (or
    ``"inactive_match"`` if ``include_inactive`` is set) and a valid
    ``@drivenets.com`` email. The username is derived from the email
    local part via :func:`derive_username_from_email`, which keeps the
    rules centralised and consistent with the rename migration.
    """

    cache = _load_email_cache(cache_path)
    accept = {"matched"}
    if include_inactive:
        accept.add("inactive_match")

    plan: List[Dict[str, str]] = []
    skipped_status: List[Tuple[str, str, str]] = []  # (cache_key, status, display)
    invalid: List[Tuple[str, str, str]] = []         # (cache_key, email, reason)

    for cache_key, entry in cache.items():
        status = entry.get("status")
        display_name = entry.get("display_name") or cache_key
        email = (entry.get("email") or "").strip().lower()
        if status not in accept:
            skipped_status.append((cache_key, status or "?", display_name))
            continue
        if not is_company_email(email):
            invalid.append((cache_key, email, "not a verified @drivenets.com email"))
            continue
        try:
            username = derive_username_from_email(email)
        except InvalidIdentityError as exc:
            invalid.append((cache_key, email, str(exc)))
            continue
        if use_legacy_password:
            chosen_password = _password_for(display_name, username)
        else:
            chosen_password = password or UNIFIED_DEFAULT_PASSWORD
        plan.append({
            "username": username,
            "email": email,
            "display_name": display_name,
            "role": ROLE_OVERRIDES.get(display_name, "engineer"),
            "password": chosen_password,
            "source_key": cache_key,
        })

    seen: Dict[str, str] = {}
    duplicates: List[Tuple[str, str, str]] = []  # (username, source_a, source_b)
    for row in plan:
        prev = seen.get(row["username"])
        if prev:
            duplicates.append((row["username"], prev, row["source_key"]))
        else:
            seen[row["username"]] = row["source_key"]

    print(f"[INFO] Cache rows accepted: {len(plan)}")
    print(f"[INFO] Cache rows skipped (status not in {sorted(accept)}): "
          f"{len(skipped_status)}")
    print(f"[INFO] Invalid email/local part rows:                       {len(invalid)}")
    print(f"[INFO] Duplicate target usernames within plan:              {len(duplicates)}")
    if duplicates:
        print("[ERROR] Refusing to seed: duplicate target usernames detected:")
        for u, a, b in duplicates:
            print(f"   - {u}: from {a} and {b}")
        sys.exit(2)

    created = 0
    skipped = 0
    errors = 0
    for u in plan:
        existing = user_store.get_user(u["username"])
        if dry_run:
            tag = "SKIP (exists)" if existing else "CREATE"
            print(f"  [{tag}] {u['username']:30s} <{u['email']}> "
                  f"({u['role']}) - {u['display_name']}")
            if existing:
                skipped += 1
            else:
                created += 1
            continue
        if existing:
            skipped += 1
            continue
        try:
            user_store.create_user(
                username=u["username"],
                password=u["password"],
                display_name=u["display_name"],
                email=u["email"],
                role=u["role"],
            )
            created += 1
            print(f"  [OK] Created {u['username']} <{u['email']}> ({u['role']})")
        except Exception as exc:  # noqa: BLE001
            errors += 1
            print(f"  [ERROR] {u['username']}: {exc}")

    print(f"\n[DONE] Created: {created}, Skipped: {skipped}, Errors: {errors}")


def main():
    parser = argparse.ArgumentParser(description="Seed DriveNets employees into topology user DB")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be created")
    parser.add_argument("--list", action="store_true", help="Print username/password table")
    parser.add_argument("--csv", type=str, help="Import from CSV file instead of hardcoded list")
    parser.add_argument("--from-email-cache", type=str,
                        help="Seed from email_resolver JSON cache (preferred mode).")
    parser.add_argument("--include-inactive", action="store_true",
                        help="With --from-email-cache, also accept 'inactive_match' rows.")
    parser.add_argument("--password", type=str, default=None,
                        help=f"Override unified password (default: "
                             f"{UNIFIED_DEFAULT_PASSWORD!r}).")
    parser.add_argument("--legacy-password", action="store_true",
                        help="Use the legacy sanitised-last-name password "
                             "convention instead of the unified password.")
    args = parser.parse_args()

    if args.from_email_cache:
        seed_from_email_cache(
            Path(args.from_email_cache).expanduser(),
            dry_run=args.dry_run,
            include_inactive=args.include_inactive,
            password=args.password,
            use_legacy_password=args.legacy_password,
        )
        return
    if args.csv:
        seed_from_csv(args.csv, dry_run=args.dry_run)
    else:
        seed_all(dry_run=args.dry_run, show_list=args.list)


if __name__ == "__main__":
    main()
