import shap


def explain_prediction(model, features, feature_names):
    """
    Explain an Isolation Forest prediction using SHAP.
    """

    explainer = shap.TreeExplainer(model)

    shap_values = explainer.shap_values(features)

    values = shap_values[0]

    explanations = []

    for name, value in zip(feature_names, values):
        explanations.append({
            "feature": name,
            "shap_value": float(value),
            "importance": abs(float(value))
        })

    explanations.sort(
        key=lambda x: x["importance"],
        reverse=True
    )

    return explanations