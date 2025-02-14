import requests, os
from utils.cache import get_last_queued_id_from_file, write_last_queued_id_to_file
from utils.telegram import send_telegram_message
from dotenv import load_dotenv

load_dotenv()

# If more project start to use tally, extract tally code to utils
TALLY_API_KEY = os.getenv("TALLY_API_KEY")
TALLY_API_URL = "https://api.tally.xyz/query"
COMPOUND_TALLY_URL = "https://www.tally.xyz/gov/compound/proposal/"

PROTOCOL = "comp"  # must be lower case
max_length_summary = 450


def extract_summary_from_description(description):
    # Extract the summary part
    summary_start = description.find("# Summary")
    if summary_start == -1:
        summary_start = description.find("## Proposal summary")
    motivation_start = description.find("# Motivation")
    if motivation_start == -1:
        motivation_start = description.find("## Proposal Action")
    summary = ""
    if summary_start != -1 and motivation_start != -1:
        summary_start = description.find("\n", summary_start)
        summary = description[summary_start:motivation_start].strip()
        summary = summary.replace("\n\n", "\n")
        # Truncate the summary if it exceeds max_length
        if len(summary) > max_length_summary:
            summary = summary[:max_length_summary].rsplit(" ", 1)[0] + "..."
    return summary


def get_proposals():
    headers = {"Api-Key": TALLY_API_KEY, "Content-Type": "application/json"}

    query = """
    query GovernanceProposals($input: ProposalsInput!) {
      proposals(input: $input) {
        nodes {
          ... on Proposal {
            id
            onchainId
            status
            createdAt
            metadata {
              title
              description
            }
          }
        }
      }
    }
    """

    variables = {
        "input": {
            "filters": {"organizationId": "2206072050458560433"},
            "sort": {"sortBy": "id", "isDescending": True},
            "page": {"limit": 10},
        }
    }

    try:
        response = requests.post(
            TALLY_API_URL,
            json={"query": query, "variables": variables},
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()

        if "errors" in data:
            raise Exception(f"GraphQL errors: {data['errors']}")

        proposals = data["data"]["proposals"]["nodes"]
        queued_proposals = [p for p in proposals if p["status"] == "queued"]
        if not queued_proposals:
            print("No queued proposals found")
            return

        print(f"Found {len(queued_proposals)} queued proposals")

        last_reported_id = get_last_queued_id_from_file(PROTOCOL)
        newest_queued_proposal_id = int(queued_proposals[0]["onchainId"])
        if newest_queued_proposal_id <= last_reported_id:
            print(f"No new proposals, last reported id: {last_reported_id}")
            return

        message = "🖋️ Compound Governance Proposals 🖋️\n"
        for proposal in queued_proposals:
            proposal_id = int(proposal["onchainId"])
            if proposal_id <= last_reported_id:
                break

            link = COMPOUND_TALLY_URL + str(proposal_id)
            message += f"📗 Proposal ID: {proposal_id}\n"
            message += f"🔗 Link to Proposal: {link}\n"

            metadata = proposal["metadata"]
            title = metadata["title"]
            description = metadata["description"]
            if title:
                message += f"📝 Title: {title}\n"
            if description:
                summary = extract_summary_from_description(description)
                if summary:
                    message += f"📝 Description: {summary}\n\n"

        send_telegram_message(message, PROTOCOL)
        # write the last reported id
        last_reported_id = int(queued_proposals[0]["onchainId"])
        write_last_queued_id_to_file(PROTOCOL, last_reported_id)

    except Exception as e:
        print(f"Error fetching proposals: {e}")
        return None


if __name__ == "__main__":
    get_proposals()
