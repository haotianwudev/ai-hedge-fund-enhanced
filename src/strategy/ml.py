import pandas as pd
import numpy as np
from typing import Tuple, List, Dict, Any
from sklearn.preprocessing import StandardScaler, MinMaxScaler, RobustScaler
from sklearn.metrics import (
    accuracy_score, roc_auc_score, classification_report, 
    confusion_matrix, roc_curve, precision_recall_curve, 
    average_precision_score
)
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
import xgboost as xgb
import matplotlib.pyplot as plt
import seaborn as sns

def split_data(X: pd.DataFrame, y: pd.Series, train_ratio: float = 0.6, val_ratio: float = 0.2) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]:
    """
    Split data into training, validation, and test sets using time-based splitting to avoid look-ahead bias.
    
    Args:
        X (pd.DataFrame): Features DataFrame
        y (pd.Series): Target Series
        train_ratio (float, optional): Ratio of data to use for training. Defaults to 0.6.
        val_ratio (float, optional): Ratio of data to use for validation. Defaults to 0.2.
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.Series, pd.Series, pd.Series]: 
            X_train, X_val, X_test, y_train, y_val, y_test
    """
    total_rows = len(X)
    train_size = int(total_rows * train_ratio)
    val_size = int(total_rows * val_ratio)
    
    # Time-based split to avoid look-ahead bias
    X_train = X.iloc[:train_size]
    X_val = X.iloc[train_size:train_size + val_size]
    X_test = X.iloc[train_size + val_size:]
    
    y_train = y.iloc[:train_size]
    y_val = y.iloc[train_size:train_size + val_size]
    y_test = y.iloc[train_size + val_size:]
    
    print(f"Training set: {X_train.shape[0]} samples from {X_train.index.min().date()} to {X_train.index.max().date()}")
    print(f"Validation set: {X_val.shape[0]} samples from {X_val.index.min().date()} to {X_val.index.max().date()}")
    print(f"Test set: {X_test.shape[0]} samples from {X_test.index.min().date()} to {X_test.index.max().date()}")
    
    # Check class distribution in each set
    print(f"\nCrash events in training set: {y_train.sum()} ({y_train.mean():.2%})")
    print(f"Crash events in validation set: {y_val.sum()} ({y_val.mean():.2%})")
    print(f"Crash events in test set: {y_test.sum()} ({y_test.mean():.2%})")
    
    return X_train, X_val, X_test, y_train, y_val, y_test

def normalize_data(X_train: pd.DataFrame, X_val: pd.DataFrame, X_test: pd.DataFrame, scaler_type: str = 'robust') -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, object]:
    """
    Normalize the data using the specified scaler type. Fits the scaler on training data only
    to prevent data leakage.
    
    Args:
        X_train (pd.DataFrame): Training features
        X_val (pd.DataFrame): Validation features
        X_test (pd.DataFrame): Test features
        scaler_type (str, optional): Type of scaler to use ('robust', 'standard', 'minmax'). Defaults to 'robust'.
            - 'robust': Uses median and IQR, best for financial data with outliers
            - 'standard': Uses mean and std, good for normally distributed data
            - 'minmax': Scales to a fixed range, good when you need bounded values
        
    Returns:
        Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, object]: 
            X_train_scaled, X_val_scaled, X_test_scaled, fitted_scaler
    """
    print("\nNormalizing data...")
    
    # Select scaler based on type
    if scaler_type == 'robust':
        scaler = RobustScaler()
        print("Using RobustScaler (median and IQR) - recommended for financial data with outliers")
    elif scaler_type == 'standard':
        scaler = StandardScaler()
        print("Using StandardScaler (mean and std) - good for normally distributed data")
    elif scaler_type == 'minmax':
        scaler = MinMaxScaler()
        print("Using MinMaxScaler (bounded range) - good when you need values in a specific range")
    else:
        raise ValueError(f"Unknown scaler type: {scaler_type}. Choose from ['robust', 'standard', 'minmax']")
    
    # Fit scaler on training data only
    X_train_scaled = pd.DataFrame(
        scaler.fit_transform(X_train),
        columns=X_train.columns,
        index=X_train.index
    )
    
    # Transform validation and test data using the fitted scaler
    X_val_scaled = pd.DataFrame(
        scaler.transform(X_val),
        columns=X_val.columns,
        index=X_val.index
    )
    
    X_test_scaled = pd.DataFrame(
        scaler.transform(X_test),
        columns=X_test.columns,
        index=X_test.index
    )
    
    print(f"Training set shape: {X_train_scaled.shape}")
    print(f"Validation set shape: {X_val_scaled.shape}")
    print(f"Test set shape: {X_test_scaled.shape}")
    
    return X_train_scaled, X_val_scaled, X_test_scaled, scaler

def tune_hyperparameters(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    model_type: str,
    n_splits: int = 3,
    n_jobs: int = -1,
    show_cv_plot: bool = False,
    param_grid: Dict[str, Any] = None
) -> Tuple[Any, float, Dict[str, Any]]:
    """
    Tune hyperparameters for the specified model type using time-series cross-validation.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        model_type: Type of model to tune ('logistic', 'rf', 'gb', 'xgb')
        n_splits: Number of splits for time-series cross-validation. Defaults to 3.
        n_jobs: Number of jobs to run in parallel. Defaults to -1 (use all processors).
        show_cv_plot: Whether to show cross-validation scores plot. Defaults to False.
        param_grid: Parameter grid for the model type
        
    Returns:
        Tuple[Any, float, Dict[str, Any]]: 
            best_model, best_val_score, best_params
    """
    print(f"\nTuning hyperparameters for {model_type} model...")
    
    # Calculate class weight for imbalanced data
    class_weight = sum(y_train==0)/sum(y_train==1)
    
    # Define parameter grids for each model type
    if param_grid is None:
        param_grids = {
            'logistic': {
                'C': [0.001, 0.01, 0.1, 1, 10, 100],
                'class_weight': ['balanced', None],
                'max_iter': [3000],
                'solver': ['liblinear'],
                'penalty': ['l1', 'l2']
            },
            'rf': {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7, 10],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'class_weight': ['balanced', 'balanced_subsample', None],
                'max_features': ['sqrt', 'log2'],
                'bootstrap': [True],
                'criterion': ['gini', 'entropy']
            },
            'gb': {
                'n_estimators': [100, 200, 300],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'subsample': [0.8, 1.0],
                'loss': ['deviance', 'exponential'],
                'max_features': ['sqrt', 'log2'],
                'criterion': ['friedman_mse', 'squared_error']
            },
            'xgb': {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0],
                'min_child_weight': [1, 3, 5],
                'gamma': [0, 0.1, 0.2],
                'reg_alpha': [0, 0.1, 1],
                'reg_lambda': [0.1, 1, 5],
                'scale_pos_weight': [1, class_weight]
            }
        }
        param_grid = param_grids[model_type]
    
    # Select model and parameter grid
    if model_type == 'logistic':
        model = LogisticRegression(random_state=42)
    elif model_type == 'rf':
        model = RandomForestClassifier(random_state=42)
    elif model_type == 'gb':
        model = GradientBoostingClassifier(random_state=42)
    elif model_type == 'xgb':
        model = xgb.XGBClassifier(
            use_label_encoder=False,
            eval_metric='logloss',
            random_state=42,
            tree_method='hist'  # Faster training
        )
    else:
        raise ValueError(f"Unknown model type: {model_type}. Choose from ['logistic', 'rf', 'gb', 'xgb']")
    
    # Create time series cross-validation splitter
    tscv = TimeSeriesSplit(n_splits=n_splits)
    
    # Create grid search with time series cross-validation
    grid_search = GridSearchCV(
        estimator=model,
        param_grid=param_grid,
        cv=tscv,
        scoring='roc_auc',
        n_jobs=n_jobs,
        verbose=1
    )
    
    # Fit grid search
    grid_search.fit(X_train, y_train)
    
    # Get best model and parameters
    best_model = grid_search.best_estimator_
    best_params = grid_search.best_params_
    best_val_score = grid_search.best_score_
    
    # Evaluate best model on validation set
    val_score = roc_auc_score(y_val, best_model.predict_proba(X_val)[:, 1])
    
    print(f"\nBest parameters: {best_params}")
    print(f"Best cross-validation score: {best_val_score:.4f}")
    print(f"Validation set score: {val_score:.4f}")
    
    # Plot cross-validation results if requested
    if show_cv_plot:
        # Get top 10 parameter combinations by score
        cv_results = pd.DataFrame(grid_search.cv_results_)
        top_results = cv_results.nlargest(10, 'mean_test_score')
        
        plt.figure(figsize=(10, 6))
        plt.bar(range(len(top_results)), top_results['mean_test_score'])
        plt.title(f'{model_type.upper()} - Top 10 Cross-validation Scores')
        plt.xlabel('Parameter Combination')
        plt.ylabel('ROC AUC Score')
        
        # Add parameter values as x-tick labels
        param_labels = []
        for _, row in top_results.iterrows():
            params = {k: v for k, v in row.items() if k.startswith('param_')}
            label = '\n'.join(f'{k[6:]}: {v}' for k, v in params.items())
            param_labels.append(label)
        
        plt.xticks(range(len(top_results)), param_labels, rotation=45, ha='right')
        plt.tight_layout()
        plt.show()
        plt.close()
    
    return best_model, val_score, best_params

def train_and_evaluate_model(
    model: Any,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_name: str,
    save_plots: bool = False,
    plot_dir: str = "logs"
) -> Tuple[Any, np.ndarray, Dict[str, float]]:
    """
    Train, evaluate and plot results for a classification model with overfitting analysis.
    
    Args:
        model: The model to train (must have fit, predict, and predict_proba methods)
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        X_test: Test features
        y_test: Test labels
        model_name: Name of the model for display purposes
        save_plots: Whether to save plots to disk. Defaults to False.
        plot_dir: Directory to save plots if save_plots is True. Defaults to "logs".
        
    Returns:
        Tuple[Any, np.ndarray, Dict[str, float]]: 
            trained_model, test_predicted_probabilities, overfitting_report
    """
    # Train the model
    model.fit(X_train, y_train)
    
    # Make predictions on all datasets
    y_train_pred = model.predict(X_train)
    y_train_prob = model.predict_proba(X_train)[:, 1]
    
    y_val_pred = model.predict(X_val)
    y_val_prob = model.predict_proba(X_val)[:, 1]
    
    y_test_pred = model.predict(X_test)
    y_test_prob = model.predict_proba(X_test)[:, 1]
    
    # Calculate metrics for all datasets
    train_accuracy = accuracy_score(y_train, y_train_pred)
    val_accuracy = accuracy_score(y_val, y_val_pred)
    test_accuracy = accuracy_score(y_test, y_test_pred)
    
    train_roc_auc = roc_auc_score(y_train, y_train_prob)
    val_roc_auc = roc_auc_score(y_val, y_val_prob)
    test_roc_auc = roc_auc_score(y_test, y_test_prob)
    
    # Print overfitting analysis
    print(f"\n{model_name} - Overfitting Analysis:")
    print(f"  Training set - Accuracy: {train_accuracy:.4f}, ROC AUC: {train_roc_auc:.4f}")
    print(f"  Validation set - Accuracy: {val_accuracy:.4f}, ROC AUC: {val_roc_auc:.4f}")
    print(f"  Test set - Accuracy: {test_accuracy:.4f}, ROC AUC: {test_roc_auc:.4f}")
    
    # Calculate overfitting metrics
    train_val_acc_diff = train_accuracy - val_accuracy
    train_test_acc_diff = train_accuracy - test_accuracy
    train_val_auc_diff = train_roc_auc - val_roc_auc
    train_test_auc_diff = train_roc_auc - test_roc_auc
    
    print(f"  Accuracy Gap (Train-Val): {train_val_acc_diff:.4f}, (Train-Test): {train_test_acc_diff:.4f}")
    print(f"  ROC AUC Gap (Train-Val): {train_val_auc_diff:.4f}, (Train-Test): {train_test_auc_diff:.4f}")
    
    # Print classification report for test set
    print(f"\n{model_name} - Test Set Classification Report:")
    print(classification_report(y_test, y_test_pred))
    
    # Plot confusion matrix
    plt.figure(figsize=(8, 6))
    cm = confusion_matrix(y_test, y_test_pred)
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['No Crash', 'Crash'], 
                yticklabels=['No Crash', 'Crash'])
    plt.title(f'{model_name} - Confusion Matrix')
    plt.ylabel('True Label')
    plt.xlabel('Predicted Label')
    plt.tight_layout()
    if save_plots:
        plt.savefig(f"{plot_dir}/{model_name.lower().replace(' ', '_')}_confusion_matrix.png")
    plt.show()
    plt.close()
    
    # Plot ROC curves for all datasets to visualize overfitting
    plt.figure(figsize=(10, 8))
    
    # Training set ROC
    fpr_train, tpr_train, _ = roc_curve(y_train, y_train_prob)
    plt.plot(fpr_train, tpr_train, 'b-', label=f'Training (AUC = {train_roc_auc:.2f})')
    
    # Validation set ROC
    fpr_val, tpr_val, _ = roc_curve(y_val, y_val_prob)
    plt.plot(fpr_val, tpr_val, 'g-', label=f'Validation (AUC = {val_roc_auc:.2f})')
    
    # Test set ROC
    fpr_test, tpr_test, _ = roc_curve(y_test, y_test_prob)
    plt.plot(fpr_test, tpr_test, 'r-', label=f'Test (AUC = {test_roc_auc:.2f})')
    
    # Reference line
    plt.plot([0, 1], [0, 1], 'k--', lw=2)
    
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(f'{model_name} - ROC Curves (Overfitting Analysis)')
    plt.legend(loc="lower right")
    if save_plots:
        plt.savefig(f"{plot_dir}/{model_name.lower().replace(' ', '_')}_roc_curve.png")
    plt.show()
    plt.close()
    
    # Plot precision-recall curve for test set
    plt.figure(figsize=(8, 6))
    precision, recall, _ = precision_recall_curve(y_test, y_test_prob)
    avg_precision = average_precision_score(y_test, y_test_prob)
    
    plt.plot(recall, precision, lw=2, label=f'Precision-Recall (AP = {avg_precision:.2f})')
    plt.axhline(y=y_test.mean(), color='r', linestyle='--', 
                label=f'Baseline (Class frequency: {y_test.mean():.2%})')
    
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('Recall')
    plt.ylabel('Precision')
    plt.title(f'{model_name} - Precision-Recall Curve')
    plt.legend(loc="best")
    if save_plots:
        plt.savefig(f"{plot_dir}/{model_name.lower().replace(' ', '_')}_precision_recall.png")
    plt.show()
    plt.close()
    
    # For tree-based models, plot feature importance
    if hasattr(model, 'feature_importances_'):
        # Get feature importances
        importances = model.feature_importances_
        indices = np.argsort(importances)[::-1]
        features = X_train.columns
        
        # Plot feature importances
        plt.figure(figsize=(12, 8))
        plt.title(f'{model_name} - Feature Importances')
        plt.bar(range(X_train.shape[1]), importances[indices], align='center')
        plt.xticks(range(X_train.shape[1]), [features[i] for i in indices], rotation=90)
        plt.tight_layout()
        if save_plots:
            plt.savefig(f"{plot_dir}/{model_name.lower().replace(' ', '_')}_feature_importance.png")
        plt.show()
        plt.close()
    
    # Create overfitting report
    overfitting_report = {
        'train_accuracy': train_accuracy,
        'val_accuracy': val_accuracy,
        'test_accuracy': test_accuracy,
        'train_roc_auc': train_roc_auc,
        'val_roc_auc': val_roc_auc,
        'test_roc_auc': test_roc_auc,
        'train_val_acc_diff': train_val_acc_diff,
        'train_test_acc_diff': train_test_acc_diff,
        'train_val_auc_diff': train_val_auc_diff,
        'train_test_auc_diff': train_test_auc_diff
    }
    
    return model, y_test_prob, overfitting_report

def train_and_evaluate_all_models(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_val: pd.DataFrame,
    y_val: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    model_types: List[str] = ['logistic', 'rf', 'gb', 'xgb'],
    fast_mode: bool = False
) -> Dict[str, Tuple[Any, np.ndarray, Dict[str, float], Dict[str, Any]]]:
    """
    Train and evaluate multiple models in sequence.
    
    Args:
        X_train: Training features
        y_train: Training labels
        X_val: Validation features
        y_val: Validation labels
        X_test: Test features
        y_test: Test labels
        model_types: List of model types to train. Defaults to ['logistic', 'rf', 'gb', 'xgb']
        fast_mode: If True, uses fewer hyperparameters and CV splits for faster results
        
    Returns:
        Dict[str, Tuple[Any, np.ndarray, Dict[str, float], Dict[str, Any]]]: 
            Dictionary mapping model names to (model, test_probabilities, overfitting_report, best_params)
    """
    # Define parameter grids for each model type
    if fast_mode:
        param_grids = {
            'logistic': {
                'C': [0.1, 1, 10],
                'class_weight': ['balanced'],
                'max_iter': [3000],
                'solver': ['liblinear'],
                'penalty': ['l2']
            },
            'rf': {
                'n_estimators': [100, 200],
                'max_depth': [5, 10],
                'min_samples_split': [2, 5],
                'class_weight': ['balanced'],
                'max_features': ['sqrt']
            },
            'gb': {
                'n_estimators': [100, 200],
                'learning_rate': [0.1],
                'max_depth': [5],
                'subsample': [0.8],
                'max_features': ['sqrt']
            },
            'xgb': {
                'n_estimators': [100, 200],
                'max_depth': [5],
                'learning_rate': [0.1],
                'subsample': [0.8],
                'colsample_bytree': [0.8]
            }
        }
        n_splits = 2  # Fewer CV splits for faster results
    else:
        param_grids = {
            'logistic': {
                'C': [0.001, 0.01, 0.1, 1, 10, 100],
                'class_weight': ['balanced', None],
                'max_iter': [3000],
                'solver': ['liblinear'],
                'penalty': ['l1', 'l2']
            },
            'rf': {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7, 10],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'class_weight': ['balanced', 'balanced_subsample', None],
                'max_features': ['sqrt', 'log2'],
                'bootstrap': [True],
                'criterion': ['gini', 'entropy']
            },
            'gb': {
                'n_estimators': [100, 200, 300],
                'learning_rate': [0.01, 0.1, 0.2],
                'max_depth': [3, 5, 7],
                'min_samples_split': [2, 5, 10],
                'min_samples_leaf': [1, 2, 4],
                'subsample': [0.8, 1.0],
                'loss': ['deviance', 'exponential'],
                'max_features': ['sqrt', 'log2'],
                'criterion': ['friedman_mse', 'squared_error']
            },
            'xgb': {
                'n_estimators': [100, 200, 300],
                'max_depth': [3, 5, 7],
                'learning_rate': [0.01, 0.1, 0.2],
                'subsample': [0.8, 1.0],
                'colsample_bytree': [0.8, 1.0],
                'min_child_weight': [1, 3, 5],
                'gamma': [0, 0.1, 0.2],
                'reg_alpha': [0, 0.1, 1],
                'reg_lambda': [0.1, 1, 5],
                'scale_pos_weight': [1, class_weight]
            }
        }
        n_splits = 3  # More CV splits for better results
    
    results = {}
    
    for model_type in model_types:
        print(f"\nTraining {model_type.upper()} model...")
        
        # Tune hyperparameters
        model, val_score, params = tune_hyperparameters(
            X_train, y_train, X_val, y_val, model_type,
            n_splits=n_splits,
            param_grid=param_grids[model_type]
        )
        
        print(f"Best parameters for {model_type}: {params}")
        
        # Train and evaluate using the model with best parameters
        model, probs, overfitting_report = train_and_evaluate_model(
            model, X_train, y_train, X_val, y_val, X_test, y_test,
            f"{model_type.upper()} (params: {params})"
        )
        
        # Store results including best parameters
        results[model_type] = (model, probs, overfitting_report, params)
    
    return results
