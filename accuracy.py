from datetime import datetime
import numpy as np
import pandas as pd

from a4s_eval.data_model.evaluation import DataShape, Dataset, Model
from a4s_eval.data_model.measure import Measure
from a4s_eval.metric_registries.model_metric_registry import model_metric
from a4s_eval.service.model_functional import FunctionalModel


@model_metric(name="accuracy")
def accuracy(
    datashape: DataShape,
    model: Model,
    dataset: Dataset,
    functional_model: FunctionalModel,
) -> list[Measure]:
    data = dataset.data
    
    
    # Extract feature names
    feature_names = [feature.name for feature in datashape.features]
    
    # Extract features (X) and target (y)
    X = data[feature_names].values
    y = data[datashape.target.name].values
    
    # Get predictions from the functional model
    y_pred = functional_model.predict(X)
    
    # Calculate accuracy manually
    correct_predictions = (y_pred == y).sum()
    total_predictions = len(y)
    accuracy_value = correct_predictions / total_predictions
    
    current_time = datetime.now()
    return [Measure(name="accuracy", score=accuracy_value, time=current_time)]
