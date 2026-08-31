import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

def main():
    data = {
        'Model': [
            'Persistence',
            'Constant Velocity',
            'Physics Model A',
            'Physics Model B',
            'Vanilla LSTM',
            'Physics + Residual LSTM',
            'Regime Hybrid'
        ],
        'Mean_EPE_m': [
            17089.97,
            15101.83,
            15855.45,
            14279.72,
            19234.16,
            19535.51,
            13125.16
        ]
    }
    df = pd.DataFrame(data)
    df = df.sort_values('Mean_EPE_m')
    
    docs_dir = Path('docs')
    figs_dir = docs_dir / 'figures'
    df.to_csv(docs_dir / 'final_model_comparison.csv', index=False)
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=df, x='Model', y='Mean_EPE_m', hue='Model', palette='viridis', legend=False)
    plt.ylabel('Mean Endpoint Error (meters)')
    plt.title('Final Model Selection: Test Set Mean EPE')
    plt.xticks(rotation=45, ha='right')
    
    for i, v in enumerate(df['Mean_EPE_m']):
        plt.text(i, v + 150, f"{v:.0f} m", ha='center', va='bottom')
        
    plt.tight_layout()
    plt.savefig(figs_dir / 'final_model_comparison.png', dpi=300)
    plt.close()

if __name__ == '__main__':
    main()
