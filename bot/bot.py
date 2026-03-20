import asyncio
import sys
from services.lms_client import LMSClient

lms = LMSClient()

async def run_query(query: str):
    query = query.lower().strip()

    if "labs are available" in query:
        labs = lms.get_items()
        labs_list = [f"{i+1}: {lab['title']}" for i, lab in enumerate(labs) if lab["type"] == "lab"]
        return "\n".join(labs_list)

    elif "lowest pass rate" in query:
        labs = [lab for lab in lms.get_items() if lab["type"] == "lab"]
        min_rate = 101
        min_lab_title = "N/A"
        for lab in labs:
            tasks = lms.get_pass_rates(lab["id"])
            if not tasks:
                continue
            avg = sum(t["pass_rate"] for t in tasks) / len(tasks)
            if avg < min_rate:
                min_rate = avg
                min_lab_title = lab["title"]
        return f"Lab with lowest pass rate: {min_lab_title} ({min_rate}%)"

    elif "which group is doing best" in query:
        lab_id = int(query.split("lab")[-1].strip())
        groups = lms.get_groups(lab_id)
        if not groups:
            return f"No group data found for Lab {lab_id}."
        top_group = max(groups, key=lambda g: g.get("avg_score", 0))
        return f"Top group for Lab {lab_id}: {top_group['name']} ({top_group.get('avg_score',0)})"

    elif "show me scores for lab" in query:
        lab_id = int(query.split("lab")[-1].strip())
        tasks = lms.get_pass_rates(lab_id)
        if not tasks:
            return f"No scores found for Lab {lab_id}."
        formatted = [f"{t['task']} — {t['pass_rate']}" for t in tasks]
        return f"Scores for Lab {lab_id}:\n" + "\n".join(formatted)

    elif "hello" in query:
        return "Hello! I can show labs, scores, pass rates, and top groups."
    else:
        return "Query not recognized. Try asking about labs, scores, or groups."


if __name__ == "__main__":
    query = " ".join(sys.argv[1:]) if len(sys.argv) > 1 else input("Enter query: ")
    result = asyncio.run(run_query(query))
    print(result)
