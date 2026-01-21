from app.store.pg_vector import PGVectorStore
from app.embeddings import get_embeddings
from app.utils import load_jsonl
from app.evaluators.retrieval.retrieval import TestQuestion, RetrievalEvaluator


def evaluate_retrieval_single_question():

    vs = PGVectorStore(embeddings=get_embeddings())
    rows = load_jsonl("app/queries/queries.jsonl")
    test_question = TestQuestion.model_validate(rows[10])

    print(test_question.model_dump_json(indent=2))

    documents = vs.get(test_question.question)
    print(documents)

    evaluator = RetrievalEvaluator(min_keyword_hits=2)
    metrics = evaluator.evaluate(test_question, documents)
    print(metrics.model_dump_json(indent=2))


def evaluate_batch_queries():

    queries = load_jsonl("app/queries/queries.jsonl")

    vs = PGVectorStore(embeddings=get_embeddings())
    evaluator = RetrievalEvaluator(min_keyword_hits=2)
    i = 1
    metrics_to_plot = []
    for q in queries:
        test_question = TestQuestion.model_validate(q)
        print(f"=========================Evaluating Question {i}===========================")
        documents = vs.get(test_question.question)
        metrics = evaluator.evaluate(test_question, documents)
        metrics_to_plot.append({
            "id": test_question.id,
            "question": test_question.question,
            "metrics": metrics.model_dump(),
        })
        i += 1
    from app.evaluators.retrieval.plot import generate_retrieval_report
    generate_retrieval_report(metrics_to_plot, out_dir="plots/retrieval", show=False)