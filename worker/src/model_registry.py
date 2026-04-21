from models.logistic_regression import predict as logistic_regression_predict
from models.decision_tree_сlassifier import predict as decision_tree_classifier_predict
from models.linear_regression import predict as linear_regression_predict

LM_MODELS = {
    "LOGISTIC": logistic_regression_predict,
    "TREE": decision_tree_classifier_predict,
    "LINEAR": linear_regression_predict,
}

def predict(ml_model: str, data):
    if ml_model not in LM_MODELS:
        raise ValueError(f"Unknown model: {ml_model}")

    predictor = LM_MODELS[ml_model]
    return predictor(data)
