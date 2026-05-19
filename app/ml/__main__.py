from app.ml.train import train_model

if __name__ == "__main__":
    metrics = train_model()
    print(f"trained: f1={metrics['f1']:.3f} precision={metrics['precision']:.3f} recall={metrics['recall']:.3f}")
