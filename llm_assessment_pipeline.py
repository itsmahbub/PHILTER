from openai import OpenAI
import os
import json
import argparse
import re
from google import genai
from google.genai import types
import pathlib

OPENAI_MODEL = "o4-mini" # "gpt-4.1-mini"  # Specify the model you want to use
GEMINI_MODEL = "gemini-2.5-pro"  # Specify the Gemini model

chatgpt_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
gemini_client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

system_prompt = (
    "You are an expert in evaluating phishing detection research. You are given:\n"
    "1. A codebook for a specific evaluation metric (definition, possible values, and criteria)\n"
    "2. The full text of a phishing detection research paper.\n\n"
    "Your task is to evaluate the method proposed in the paper against the specified metric:\n"
    "- Base your reasoning strictly on the paper content.\n"
    "- Focus on technical and methodological sections.\n"
    "- Assign one of the allowed values from the codebook.\n"
    "- Justify your choice with an explanation.\n"
    "- Support it with direct evidence from paper.\n"
    "- Output Format:\n"
    "- Return a JSON object using this schema:"
    """```json
{
    "value": "<value">,
    "why": "<Explanation>",
    "evidence": "<page, section, supporting quote>"
}```
"""
)

def file_for_chatgpt(filename):
    file = chatgpt_client.files.create(
        file=open(filename, "rb"),
        purpose="user_data"
    )
    return file

def file_for_gemini(filename):
    return pathlib.Path(filename).read_bytes()

def read_metric_definition(metric_path):
    with open(metric_path, 'r', encoding='utf-8') as f:
        return f.read()

def evaluate_with_gemini(paper_path, metric_definition, error_message=""):

    paper_content = file_for_gemini(paper_path)
    prompt =  (
        f"Codebook:\n{metric_definition}"
    )

    response = gemini_client.models.generate_content(
        model=GEMINI_MODEL,
        config=types.GenerateContentConfig(system_instruction=system_prompt+error_message),
        contents=[
            types.Part.from_bytes(
                data=paper_content,
                mime_type='application/pdf',
            ),
            prompt
        ]
    )
    # response = gemini_client.models.generate_content(
    #     model=GEMINI_MODEL,
    #     config=types.GenerateContentConfig(system_instruction=system_prompt+error_message),
    #     contents=["Metric definition:\n" + metric_definition + "\n\nResearch Paper Text:\n" + paper_text],

    # )
    return response.text.strip()


def evaluate_with_chatgpt(paper_path, metric_definition, error_message=""):
    if not chatgpt_client.api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    paper_file = file_for_chatgpt(paper_path)
    messages = [
        {
            "role": "system",
            "content": system_prompt+ error_message

        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text":  f"Codebook:\n{metric_definition}"
                },
                {
                    "type": "input_file",
                    "file_id": paper_file.id,
                }
            ]
        }
        # {
        #     "role": "user",
        #     "content": f"Codebook:\n\n{metric_definition}"
        # },
        # {
        #     "role": "user",
        #     "content": f"Research Paper Text:\n\n{paper_text}"
        # }
    ]
    response = chatgpt_client.responses.create(
                model=OPENAI_MODEL,
                input=messages
    )
    return response.output_text.strip()

def reconcile_disagreement(metric_definition, paper_path, chatgpt_output, gemini_output, error_message=""):
    paper_file = file_for_chatgpt(paper_path)
    messages = [
        {
            "role": "system",
            "content": (
                "You are an expert resolving disagreement between two assessments:\n"
                "You are given:\n"
                " 1. A codebook for a specific evaluation metric (definition, possible values, and fulfillment criteria)\n"
                " 2. The full text of a phishing detection research paper\n"
                " 3. Two assessments with conflicting verdicts.\n\n"
                "Instructions:\n"
                "- Review both assessments using the codebook and the paper.\n"
                "- Assign a value and provide rationale.\n"
                "- Justify your conclusion with an explanation.\n"
                "- Support it with direct evidence from the paper.\n"
                "Output Format:\n"
                "- Return a JSON object using this schema:"
                """```json
{
    "value": "<value>",
    "why": "<Explanation>",
    "evidence": "<page, section, supporting quote>"
}```
""" + error_message
                
            )
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "input_text",
                    "text":  f"Codebook:\n{metric_definition}"
                },
                {
                    "type": "input_file",
                    "file_id": paper_file.id,
                },
                {
                     "type": "input_text",
                     "text": f"Evaluator A:\n{chatgpt_output}"
                },
                {
                     "type": "input_text",
                     "text": f"Evaluator B:\n{gemini_output}"
                }
            ]
        }
        # {"role": "user", "content": f"Codebook:\n{metric_definition}"},
        # {"role": "user", "content": f"Paper:\n{paper_text}"},
        # {"role": "user", "content": f"Evaluation A:\n{chatgpt_output}"},
        # {"role": "user", "content": f"Evaluation B:\n{gemini_output}"}
    ]
    response = chatgpt_client.responses.create(
                model=OPENAI_MODEL,
                input=messages
    )
    return response.output_text.strip()

def extract_verdict(llm_response):
    """
    Extract and parse the final verdict from an LLM response string.

    Parameters:
        llm_response (str): Full string response from the LLM.

    Returns:
        dict: Extracted JSON object with 'verdict' and 'reasoning'.
    """
    try:
        # Try parsing the entire response directly
        return json.loads(llm_response)
    except json.JSONDecodeError:
        pass

    try:
        # Try extracting from fenced code block
        matches = re.findall(r"```json\s*(\{.*?\})\s*```", llm_response, re.DOTALL)
        for match in reversed(matches):  # Try last block first
            try:
                return json.loads(match)
            except json.JSONDecodeError:
                continue

        raise ValueError("No valid JSON object found in the response.")

    except Exception as e:
        raise RuntimeError(f"Failed to extract response: {e}")


def process_paper_metric_pair(paper_path, metric_path, results_dir, verdicts, verdict_json_path, override, no_cache):
    paper_name = os.path.splitext(os.path.basename(paper_path))[0]
    metric_name = os.path.splitext(os.path.basename(metric_path))[0]
    try:
        paper_key = verdicts[paper_name]["key"]
    except KeyError:
        return

    if not override and paper_name in verdicts and metric_name in verdicts[paper_name] and "llm_judge" in verdicts[paper_name][metric_name]:
        print(f"Skipping {paper_name} x {metric_name} (already exists)")
        return

    metric_definition = read_metric_definition(metric_path)

    chatgpt_filename = f"{paper_key}-{metric_name}.chatgpt"
    chatgpt_path = os.path.join(results_dir, chatgpt_filename)

    if not no_cache and os.path.exists(chatgpt_path):
        with open(chatgpt_path, "r", encoding="utf-8") as f:
            chatgpt_response = f.read()
        print(f"Using cached ChatGPT response for {paper_name} x {metric_name}")
    else:
        try:
            chatgpt_response = evaluate_with_chatgpt(paper_path, metric_definition)
            extract_verdict(chatgpt_response)
        except Exception as e:
            chatgpt_response = evaluate_with_chatgpt(paper_path, metric_definition, "\nFailed to extract the JSON object from your previous response. Please ensure the response is in the correct format.")
        
        with open(chatgpt_path, "w", encoding="utf-8") as f:
            f.write(chatgpt_response)
        print(f"ChatGPT response saved to {chatgpt_path}")


    gemini_filename = f"{paper_key}-{metric_name}.gemini"
    gemini_path = os.path.join(results_dir, gemini_filename)
    if not no_cache and os.path.exists(gemini_path):
        with open(gemini_path, "r", encoding="utf-8") as f:
            gemini_response = f.read()
        print(f"Using cached Gemini response for {paper_name} x {metric_name}")
    else:
        try:
            gemini_response = evaluate_with_gemini(paper_path, metric_definition)
            extract_verdict(gemini_response)
        except Exception as e:
            gemini_response = evaluate_with_gemini(paper_path, metric_definition, "\nFailed to extract the JSON object from your previous response. Please ensure the response is in the correct format.")
    
        with open(gemini_path, "w", encoding="utf-8") as f:
            f.write(gemini_response)
        print(f"Gemini response saved to {gemini_path}")

    try:
        chatgpt_verdict = extract_verdict(chatgpt_response)
    except:
        print(f"Error : ChatGPT Evaluator : {paper_key} : {metric_name} ")
        return
    
    try:
        gemini_verdict = extract_verdict(gemini_response)
    except:
        print(f"Error : Gemini Evaluator : {paper_key} : {metric_name} ")
        return

    if chatgpt_verdict["value"] == gemini_verdict["value"]:
        final_verdict = chatgpt_verdict
    else:
        reconciled_filename = f"{paper_key}-{metric_name}.reconciled"
        reconciled_path = os.path.join(results_dir, reconciled_filename)
        if not no_cache and os.path.exists(reconciled_path):
            with open(reconciled_path, "r", encoding="utf-8") as f:
                reconciled_response = f.read()
            print(f"Using cached reconciled response for {paper_name} x {metric_name}")
        else:
            try:
                reconciled_response = reconcile_disagreement(metric_definition, paper_path, chatgpt_response, gemini_response)
                extract_verdict(reconciled_response)
            except Exception as e:
                reconciled_response = reconcile_disagreement(
                    metric_definition, paper_path, chatgpt_response, gemini_response,
                    "\nFailed to extract the JSON object from your previous response. Please ensure the response is in the correct format."
                )
            with open(reconciled_path, "w", encoding="utf-8") as f:
                f.write(reconciled_response)
            print(f"Reconciled response saved to {reconciled_path}")

        try:
            final_verdict = extract_verdict(reconciled_response)
        except:
            print(f"Error : Judge LLM : {paper_key} : {metric_name} ")
            return

    # Update verdict
    if paper_name not in verdicts:
        verdicts[paper_name] = {}
    if metric_name not in verdicts[paper_name]:
        verdicts[paper_name][metric_name] = {}
    verdicts[paper_name][metric_name]["chatgpt"] = chatgpt_verdict
    verdicts[paper_name][metric_name]["gemini"] = gemini_verdict
    verdicts[paper_name][metric_name]["arbitrator"] = final_verdict

    # Save verdicts
    with open(verdict_json_path, "w", encoding="utf-8") as f:
        json.dump(verdicts, f, indent=4)

    print(f"{paper_name} x {metric_name} => {final_verdict['value']}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--pdf-path", help="PDF file or directory")
    parser.add_argument("-m", "--metric-path", help="Metric file or directory")
    parser.add_argument("-o", "--output-json", default="assessments.json", help="Assessment output JSON file")
    parser.add_argument("--override", action="store_true", help="Override previously processed results")
    parser.add_argument("--no-cache", action="store_true", help="Invokes LLMs to recalculate verdicts, ignoring cached results")

    args = parser.parse_args()

    paper_directory = "./papers"
    results_directory = "./llm_responses"
    os.makedirs(results_directory, exist_ok=True)

    # Load verdicts
    verdict_json_path = os.path.join("./", args.output_json)
    if os.path.exists(verdict_json_path):
        with open(verdict_json_path, "r", encoding="utf-8") as f:
            verdicts = json.load(f)
    else:
        verdicts = {}

    # Get paper(s)
    if args.pdf_path.endswith(".pdf"):
        paper_paths = [os.path.join(paper_directory, args.pdf_path)]
    else:
        paper_paths = [os.path.join(paper_directory, f) for f in os.listdir(paper_directory) if f.endswith(".pdf")]

    # Get metric(s)
    if args.metric_path.endswith(".txt"):
        metric_paths = [args.metric_path]
    else:
        metric_paths = [
            os.path.join(args.metric_path, f)
            for f in os.listdir(args.metric_path)
            if f.endswith(".txt")
        ]

    # Run for all combinations
    for paper_path in paper_paths:
        for metric_path in metric_paths:
            process_paper_metric_pair(
                paper_path,
                metric_path,
                results_directory,
                verdicts,
                verdict_json_path,
                override=args.override,
                no_cache=args.no_cache
            )

    # Save assessments
    with open(verdict_json_path, "w", encoding="utf-8") as f:
        json.dump(verdicts, f, indent=2)
    print(f"Assessments saved to {verdict_json_path}")

if __name__ == "__main__":
    main()