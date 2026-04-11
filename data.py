import json
import re
import html
from collections import Counter, defaultdict
from datetime import datetime
import os

SYMPAT = {
    "fatigue": r"\bfatigue\b|\bfatigued\b",
    "extreme fatigue": r"crippling fatigue|extreme fatigue|severe fatigue|chronic fatigue|debilitating fatigue|crushing fatigue|overwhelming fatigue|exhaustion|exhausted",
    "shortness of breath": r"shortness of breath|\bsob\b|breathless|difficulty breathing|trouble breathing|hard to breathe|cant breathe|cannot breathe|\bdyspnea\b",
    "headache": r"headache|headaches|head ache|migraine",
    "chest pain": r"chest pain|chest tightness|chest pressure|chest discomfort",
    "cough": r"\bcough\b|coughing",
    "fever": r"\bfever\b|\bfevers\b|\bfebrile\b|low grade|low-grade",
    "gi issues": r"\bgi\b issues?|diarrh|constipat|stomach|gastro|bowel|ibs",
    "brain fog": r"brain fog|foggy|foggiest|cognitive|cant think|cannot think|cant focus|cannot focus|memory issue|memory problem|forgetful|brain not working",
    "anxiety": r"\banxiety\b|anxious",
    "muscle pain": r"muscle pain|myalgia|muscle ache|body ache|body pain|aching all over|achy",
    "dizziness": r"dizziness|dizzy|lightheaded",
    "palpitations": r"palpitations?|heart rac|heart pound|tachycardia|racing heart|rapid heart",
    "nausea": r"\bnausea\b|\bnauseous\b",
    "tingling/numbness": r"tingling|numbness|paresthesia|pins and needles",
    "sore throat": r"sore throat",
    "loss of taste/smell": r"loss of taste|ageusia|no taste|loss of smell|anosmia|no smell|cant taste|cannot taste|cant smell|cannot smell",
    "rash/hives": r"\brash\b|\brashes\b|\bhives\b",
    "depression": r"depression|depressed",
    "insomnia": r"insomnia|cant sleep|cannot sleep|sleep issues?|sleep problem|sleepless|trouble sleeping",
    "tinnitus": r"tinnitus|ringing in",
    "joint pain": r"joint pain|arthralgia|arthritis",
    "tremor": r"\btremor\b|\btremors\b|trembling|shaking",
    "hair loss": r"hair loss|hair falling|alopecia",
    "blood clots": r"blood clot|clot|thromb|dvt|pulmonary embol|embolism|\bpe\b.*lung",
    "pots/dysautonomia": r"\bpots\b|postural orthostatic|orthostatic|dysautonomi|dysautonomia",
    "inflammation": r"inflammat",
    "mcas/histamine": r"\bmcas\b|mast cell|histamine|intolerance",
    "costochondritis": r"costochondritis|costo",
    "vertigo": r"vertigo",
    "fibromyalgia": r"fibromyalgia|\bfibro\b",
    "chronic fatigue syndrome": r"\bcfs\b|myalgic encephalomyelitis",
    "neuropathy": r"neuropathy|peripheral nerve|nerve damage|nerve pain",
    "pulse ox concerns": r"pulse ox|oxygen level|spo2|saturation|\bo2\b level",
    "autoimmune": r"autoimmun",
    "brain pressure": r"brain pressure|head pressure|pressure in head|intracranial",
    "viral persistence": r"viral persist|persist.*virus|virus.*persist|reservoir|lingering virus",
}

MEDPAT = {
    "low dose naltrexone": r"\bldn\b|low dose naltrexone|naltrexone",
    "prednisone": r"prednisone",
    "steroids (general)": r"steroid|corticosteroid|cortisol|dexamethasone|medrol|methylprednisolone",
    "vitamin d": r"vitamin d|vit d|vitamin d3|cholecalciferol",
    "vitamin c": r"vitamin c|vit c|ascorbic",
    "omega-3/fish oil": r"omega.3|fish oil|omega3|\bepa\b|\bdha\b",
    "zinc": r"\bzinc\b",
    "antihistamines": r"antihistamine|benadryl|diphenhydramine|zyrtec|cetirizine|claritin|loratadine|allegra|fexofenadine",
    "melatonin": r"melatonin",
    "azithromycin/z-pack": r"azithromycin|z.pack|zpack|z pack",
    "acetaminophen/paracetamol": r"acetaminophen|paracetamol|tylenol",
    "ibuprofen/nsaids": r"ibuprofen|advil|motrin|nsaid|naproxen|aleve",
    "aspirin": r"\baspirin\b|baby aspirin|daily aspirin|low dose aspirin|81mg",
    "magnesium": r"magnesium",
    "b-vitamins": r"b complex|b vitamins|b12|b-12|vitamin b|methylfolate|methylcobalamin",
    "probiotics": r"probiotic|probiotics",
    "ssri/antidepressants": r"ssri|antidepressant|lexapro|zoloft|sertraline|escitalopram|prozac|fluoxetine|citalopram|celexa|paxil|paroxetine",
    "pepcid/famotidine": r"pepcid|famotidine",
    "quercetin": r"quercetin",
    "ivermectin": r"ivermectin",
    "nattokinase": r"nattokinase",
    "coq10": r"coq10|coenzyme q10|ubiquinol",
    "anti-anxiety (benzos)": r"benzo|valium|diazepam|lorazepam|ativan|xanax|alprazolam|klonopin|clonazepam",
    "blood thinners": r"blood thinner|anticoagulant|warfarin|eliquis|apixaban|xarelto|rivaroxaban|heparin|lovenox|enoxaparin",
    "curcumin/turmeric": r"curcumin|turmeric|curcuma",
    "metoprolol/beta-blockers": r"metoprolol|beta blocker|propranolol|atenolol|bisoprolol",
    "inhalers": r"inhaler|albuterol|ventolin|salbutamol|budesonide|pulmicort|flovent|fluticasone",
    "ppis": r"pump inhibitor|ppi|omeprazole|prilosec|pantoprazole|lansoprazole|esomeprazole|nexium",
    "thc/cannabis": r"\bthc\b|cannabis|marijuana|\bweed\b",
    "cbd": r"\bcbd\b|cannabidiol",
    "antibiotics": r"antibiotic|doxycycline|amoxicillin",
    "montelukast/singulair": r"singulair|montelukast",
    "guaifenesin/mucinex": r"guaifenesin|mucinex",
    "colchicine": r"colchicine",
    "hydroxychloroquine": r"hydroxychloroquine|hcq|plaquenil",
    "ashwagandha": r"ashwagandha",
    "statins": r"statin|atorvastatin|lipitor|simvastatin|rosuvastatin|crestor",
    "glutathione": r"glutathione",
    "adderall/stimulants": r"adderall|amphetamine|stimulant",
    "modafinil": r"modafinil|provigil|armodafinil|nuvigil",
    "gabapentin": r"gabapentin|gabapent|neurontin",
    "antivirals": r"antiviral|paxlovid|nirmatrelvir|remdesivir",
    "fludrocortisone": r"fludrocortisone|florinef",
    "midodrine": r"midodrine",
    "l-arginine": r"l.arginine|arginine",
    "iron": r"\biron\b|anemia|anaemia",
    "nicotine patch": r"nicotine patch",
    "nicotine (general)": r"\bnicotine\b",
    "nebulizer": r"nebuliz|nebulis",
    "blood pressure meds": r"lisinopril|amlodipine|losartan|blood pressure med",
    "thyroid meds": r"levothyroxine|synthroid|armour thyroid|thyroid.*med",
    "creatine": r"\bcreatine\b",
    "l-carnitine": r"\bcarnitine\b|acetyl.l.carnitine|\balcar\b",
    "serrapeptase": r"serrapeptase|serrazimes",
    "berberine": r"\bberberine\b",
    "sulforaphane": r"\bsulforaphane\b",
    "milk thistle": r"milk thistle|silymarin|silybin",
    "d-ribose": r"\bribose\b|d.ribose",
    "l-lysine": r"\blysine\b|l.lysine",
    "dhea": r"\bdhea\b",
    "peptides": r"\bpeptide\b|\bpeptides\b|\bbpc.157\b|\btb.500\b",
    "liposomal": r"\bliposomal\b",
    "digestive enzymes": r"\bdigestive enzyme\b",
    "hocl": r"\bhocl\b|hypochlorous",
    "ketotifen": r"\bketotifen\b",
    "cromolyn": r"\bcromolyn\b|sodium cromoglycate",
    "pregnenolone": r"\bpregnenolone\b",
    "sildenafil": r"\bsildenafil\b|\bviagra\b",
    "spironolactone": r"\bspironolactone\b",
    "fluvoxamine": r"\bfluvoxamine\b|\bluvox\b",
    "dextromethorphan": r"\bdextromethorphan\b|\bdxm\b",
}

MED_CATEGORIES = {
    "supplement": [
        "vitamin d",
        "vitamin c",
        "omega-3/fish oil",
        "zinc",
        "magnesium",
        "b-vitamins",
        "probiotics",
        "quercetin",
        "nattokinase",
        "coq10",
        "curcumin/turmeric",
        "ashwagandha",
        "glutathione",
        "l-arginine",
        "creatine",
        "l-carnitine",
        "serrapeptase",
        "berberine",
        "sulforaphane",
        "milk thistle",
        "d-ribose",
        "l-lysine",
        "dhea",
        "peptides",
        "liposomal",
        "digestive enzymes",
        "hocl",
        "ketotifen",
        "cromolyn",
        "pregnenolone",
        "melatonin",
        "iron",
        "cbd",
        "thc/cannabis",
    ],
    "otc": [
        "acetaminophen/paracetamol",
        "ibuprofen/nsaids",
        "aspirin",
        "antihistamines",
        "pepcid/famotidine",
        "ppis",
        "guaifenesin/mucinex",
        "melatonin",
        "zinc",
        "vitamin d",
        "vitamin c",
        "magnesium",
        "b-vitamins",
        "probiotics",
        "coq10",
        "curcumin/turmeric",
        "omega-3/fish oil",
        "quercetin",
        "nattokinase",
        "ashwagandha",
        "glutathione",
        "creatine",
        "l-carnitine",
        "serrapeptase",
        "berberine",
        "sulforaphane",
        "milk thistle",
        "d-ribose",
        "l-lysine",
        "dhea",
        "peptides",
        "digestive enzymes",
        "hocl",
        "ketotifen",
        "cromolyn",
        "pregnenolone",
        "cbd",
        "thc/cannabis",
        "nicotine (general)",
        "nicotine patch",
    ],
    "prescription": [
        "low dose naltrexone",
        "prednisone",
        "steroids (general)",
        "azithromycin/z-pack",
        "ssri/antidepressants",
        "ivermectin",
        "anti-anxiety (benzos)",
        "blood thinners",
        "metoprolol/beta-blockers",
        "inhalers",
        "antibiotics",
        "montelukast/singulair",
        "colchicine",
        "hydroxychloroquine",
        "statins",
        "adderall/stimulants",
        "modafinil",
        "gabapentin",
        "antivirals",
        "fludrocortisone",
        "midodrine",
        "nebulizer",
        "blood pressure meds",
        "thyroid meds",
        "sildenafil",
        "spironolactone",
        "fluvoxamine",
        "dextromethorphan",
    ],
}

DOSAGE_PAT = [
    re.compile(
        r"(?:take|taking|took|dose of|dosage of|on|started)"
        r"[^.]{0,120}"
        r"\d+\s*(?:mg|iu|mcg|ml|g\b)"
        r"[^.]{0,100}"
        r"(?:daily|per day|a day|every day|each day|every morning|every night|at night|in the morning|before bed|with food|on an empty stomach|twice|once|three times|x\s*\d|x\d|2x|3x)",
        re.IGNORECASE,
    ),
    re.compile(
        r"(?:supplement|vitamin|zinc|magnesium|melatonin|quercetin|coq10|nac|nattokinase|famotidine|pepcid|aspirin|prednisone|steroid|inhaler|ivermectin|ashwagandha|turmeric|curcumin|creatine|probiotic|omega)"
        r"[^.]{0,60}"
        r"\d+\s*(?:mg|iu|mcg|ml|g\b)"
        r"[^.]{0,60}"
        r"(?:daily|per day|a day|twice|once|x\s*\d|x\d)",
        re.IGNORECASE,
    ),
]

REGIMEN_PAT = re.compile(
    r"(?:my\s+(?:protocol|regimen|routine|stack|supplement|medication)\s+(?:is|are|includes?|consists?))|(?:i\s+(?:take|am taking|currently take)\s+(?:the\s+)?following)",
    re.IGNORECASE,
)


def extract_dosage_info(text):
    snippets = []
    for pat in DOSAGE_PAT:
        for m in pat.finditer(text):
            snippet = m.group(0).strip()
            snippet = re.sub(r"\s+", " ", snippet)
            if len(snippet) > 30:
                snippet = snippet[:200]
                snippets.append(snippet)
    for m in REGIMEN_PAT.finditer(text):
        start = m.start()
        end = min(start + 400, len(text))
        snippet = text[start:end].strip()
        snippet = re.sub(r"\s+", " ", snippet)
        snippets.append(snippet[:300])
    return snippets


def extract_theme_evidence(text, theme_name, pattern):
    matches = []
    for m in re.finditer(pattern, text):
        start = max(0, m.start() - 50)
        end = min(len(text), m.end() + 50)
        context = text[start:end].strip()
        context = re.sub(r"\s+", " ", context)
        if len(context) > 20:
            matches.append(context[:150])
    return matches[:3]


def analyze_posts(filepath, max_entries=None):
    entries = []
    with open(filepath, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_entries and i >= max_entries:
                break
            if not line.strip():
                continue
            entries.append(json.loads(line))

    posts_data = []
    symptom_counts = Counter()
    med_counts = Counter()
    theme_counts = Counter()
    specialist_counts = Counter()
    user_profiles = defaultdict(
        lambda: {
            "post_count": 0,
            "symptoms": set(),
            "medications": set(),
            "themes": set(),
            "first_post": None,
            "last_post": None,
            "scores": [],
            "total_comments": 0,
        }
    )
    monthly_counts = Counter()
    flair_counts = Counter()
    symptom_by_month = defaultdict(lambda: Counter())
    med_by_month = defaultdict(lambda: Counter())
    theme_by_month = defaultdict(lambda: Counter())
    symptom_posts = defaultdict(list)
    med_posts = defaultdict(list)
    theme_posts = defaultdict(list)
    symptom_med_cooc = Counter()
    cooc_posts = defaultdict(list)
    theme_evidence = defaultdict(list)
    dosage_info = []

    for e in entries:
        title = e.get("title", "")
        selftext = e.get("selftext", "")
        if selftext in ["[deleted]", "[removed]"]:
            selftext = ""
        combined = (title + " " + selftext).lower()
        author = e.get("author", "[deleted]")
        created = e.get("created_utc")
        score = e.get("score", 0)
        num_comments = e.get("num_comments", 0)
        flair = e.get("link_flair_text", "")
        post_id = e.get("id", "")

        post_symptoms = []
        post_meds = []
        post_themes = []
        symptom_matches = []
        med_matches = []

        month_key = None
        if created:
            dt = datetime.fromtimestamp(created)
            month_key = dt.strftime("%Y-%m")
            monthly_counts[month_key] += 1

        for sname, spat in SYMPAT.items():
            m = re.search(spat, combined)
            if m:
                symptom_counts[sname] += 1
                post_symptoms.append(sname)
                ms = max(0, m.start() - 40)
                me = min(len(combined), m.end() + 40)
                ctx = combined[ms:me].strip()
                ctx = re.sub(r"\s+", " ", ctx)
                symptom_matches.append(
                    {"key": sname, "matched": m.group(0), "context": ctx[:150]}
                )
                if month_key:
                    symptom_by_month[month_key][sname] += 1
                symptom_posts[sname].append(post_id)
                if author != "[deleted]":
                    user_profiles[author]["symptoms"].add(sname)

        for mname, mpat in MEDPAT.items():
            m = re.search(mpat, combined)
            if m:
                med_counts[mname] += 1
                post_meds.append(mname)
                ms = max(0, m.start() - 40)
                me = min(len(combined), m.end() + 40)
                ctx = combined[ms:me].strip()
                ctx = re.sub(r"\s+", " ", ctx)
                med_matches.append(
                    {"key": mname, "matched": m.group(0), "context": ctx[:150]}
                )
                if month_key:
                    med_by_month[month_key][mname] += 1
                med_posts[mname].append(post_id)
                if author != "[deleted]":
                    user_profiles[author]["medications"].add(mname)

        for tname, tpat in THEMEPAT.items():
            if re.search(tpat, combined):
                theme_counts[tname] += 1
                post_themes.append(tname)
                if month_key:
                    theme_by_month[month_key][tname] += 1
                theme_posts[tname].append(post_id)
                evidence = extract_theme_evidence(combined, tname, tpat)
                for ev in evidence:
                    theme_evidence[tname].append({"post_id": post_id, "evidence": ev})
                if author != "[deleted]":
                    user_profiles[author]["themes"].add(tname)

        for spname, sppat in SPECIALISTPAT.items():
            if re.search(sppat, combined):
                specialist_counts[spname] += 1

        if flair:
            flair_counts[flair] += 1

        if author != "[deleted]":
            up = user_profiles[author]
            up["post_count"] += 1
            up["scores"].append(score)
            up["total_comments"] += num_comments
            if up["first_post"] is None or (created and created < up["first_post"]):
                up["first_post"] = created
            if up["last_post"] is None or (created and created > up["last_post"]):
                up["last_post"] = created

        dosage_snippets = extract_dosage_info(combined)
        for snippet in dosage_snippets:
            dosage_info.append(
                {
                    "post_id": post_id,
                    "snippet": snippet,
                    "month": month_key,
                }
            )

        clean_selftext = (
            selftext.replace("\r\n", " ").replace("\n", " ").replace("\r", " ")
        )
        clean_selftext = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", clean_selftext)
        clean_selftext = re.sub(r"[\u200b\u200c\u200d\ufeff]", " ", clean_selftext)
        if len(clean_selftext) > 1500:
            clean_selftext = clean_selftext[:1500]

        posts_data.append(
            {
                "id": post_id,
                "title": title,
                "selftext": clean_selftext,
                "author": author,
                "created_utc": created,
                "score": score,
                "num_comments": num_comments,
                "flair": flair,
                "symptoms": post_symptoms,
                "medications": post_meds,
                "symptom_matches": symptom_matches,
                "med_matches": med_matches,
                "themes": post_themes,
                "permalink": e.get("permalink", ""),
            }
        )

        for s in post_symptoms:
            for m in post_meds:
                symptom_med_cooc[(s, m)] += 1
                cooc_posts[(s, m)].append(post_id)

    top_users = sorted(
        [(a, d) for a, d in user_profiles.items()],
        key=lambda x: -x[1]["post_count"],
    )

    all_months = sorted(monthly_counts.keys())

    return {
        "posts": posts_data,
        "symptom_counts": dict(symptom_counts.most_common()),
        "med_counts": dict(med_counts.most_common()),
        "theme_counts": dict(theme_counts.most_common()),
        "specialist_counts": dict(specialist_counts.most_common()),
        "flair_counts": dict(flair_counts.most_common()),
        "monthly_counts": dict(sorted(monthly_counts.items())),
        "symptom_time": {m: dict(symptom_by_month[m]) for m in all_months},
        "med_time": {m: dict(med_by_month[m]) for m in all_months},
        "theme_time": {m: dict(theme_by_month[m]) for m in all_months},
        "symptom_posts": {k: v for k, v in symptom_posts.items()},
        "med_posts": {k: v for k, v in med_posts.items()},
        "theme_posts": {k: v for k, v in theme_posts.items()},
        "theme_evidence": {k: v[:5] for k, v in theme_evidence.items()},
        "dosage_info": dosage_info,
        "symptom_med_cooc": [
            {"symptom": s, "med": m, "count": c, "post_ids": cooc_posts.get((s, m), [])}
            for (s, m), c in symptom_med_cooc.most_common(100)
        ],
        "med_categories": MED_CATEGORIES,
        "top_users": [
            (
                a,
                {
                    "post_count": d["post_count"],
                    "symptoms": list(d["symptoms"]),
                    "medications": list(d["medications"]),
                    "themes": list(d["themes"]),
                    "first_post": d["first_post"],
                    "last_post": d["last_post"],
                    "avg_score": round(sum(d["scores"]) / len(d["scores"]), 1)
                    if d["scores"]
                    else 0,
                    "total_comments": d["total_comments"],
                },
            )
            for a, d in top_users
        ],
        "total_posts": len(posts_data),
        "total_users": len(user_profiles),
    }


if __name__ == "__main__":
    data = analyze_posts("r_covidlonghaulers_posts.jsonl", max_entries=12733)
    data_json = json.dumps(data, ensure_ascii=False)
    with open("long_covid_data.js", "w", encoding="utf-8") as f:
        f.write("const DATA = ")
        f.write(data_json)
        f.write(";")
    print(f"Analyzed {data['total_posts']} posts from {data['total_users']} users")
    print(
        f"Symptoms: {len(data['symptom_counts'])}, Meds: {len(data['med_counts'])}, Themes: {len(data['theme_counts'])}"
    )
    print(
        f"Dosage snippets: {len(data['dosage_info'])}, Theme evidence keys: {len(data['theme_evidence'])}"
    )
