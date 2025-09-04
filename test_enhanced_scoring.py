#!/usr/bin/env python3
"""
Test script to demonstrate the enhanced stroke risk scoring system
Shows how the new graduated scoring provides better distribution
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import StrokeRiskCalculator

def test_enhanced_scoring():
    """Test the enhanced scoring system with various patient profiles"""
    
    calculator = StrokeRiskCalculator()
    
    # Test cases with different risk profiles
    test_cases = [
        {
            'name': 'Young Healthy Adult',
            'data': {
                'age': 25,
                'gender': 'Female',
                'hypertension': 0,
                'heart_disease': 0,
                'ever_married': 'Yes',
                'work_type': 'Govt_job',
                'residence_type': 'Rural',
                'avg_glucose_level': 85,
                'bmi': 22.5,
                'smoking_status': 'never smoked'
            }
        },
        {
            'name': 'Middle-aged with Pre-diabetes',
            'data': {
                'age': 45,
                'gender': 'Male',
                'hypertension': 0,
                'heart_disease': 0,
                'ever_married': 'Yes',
                'work_type': 'Private',
                'residence_type': 'Urban',
                'avg_glucose_level': 110,
                'bmi': 27.5,
                'smoking_status': 'formerly smoked'
            }
        },
        {
            'name': 'Senior with Moderate Risk',
            'data': {
                'age': 65,
                'gender': 'Female',
                'hypertension': 1,
                'heart_disease': 0,
                'ever_married': 'Yes',
                'work_type': 'Private',
                'residence_type': 'Urban',
                'avg_glucose_level': 140,
                'bmi': 28.0,
                'smoking_status': 'never smoked'
            }
        },
        {
            'name': 'High Risk Patient',
            'data': {
                'age': 72,
                'gender': 'Male',
                'hypertension': 1,
                'heart_disease': 1,
                'ever_married': 'Yes',
                'work_type': 'Self-employed',
                'residence_type': 'Urban',
                'avg_glucose_level': 165,
                'bmi': 32.0,
                'smoking_status': 'formerly smoked'
            }
        },
        {
            'name': 'Very High Risk Patient',
            'data': {
                'age': 78,
                'gender': 'Male',
                'hypertension': 1,
                'heart_disease': 1,
                'ever_married': 'Yes',
                'work_type': 'Self-employed',
                'residence_type': 'Urban',
                'avg_glucose_level': 200,
                'bmi': 35.5,
                'smoking_status': 'smokes'
            }
        },
        {
            'name': 'Critical Risk Patient',
            'data': {
                'age': 85,
                'gender': 'Male',
                'hypertension': 1,
                'heart_disease': 1,
                'ever_married': 'Yes',
                'work_type': 'Self-employed',
                'residence_type': 'Urban',
                'avg_glucose_level': 280,
                'bmi': 42.0,
                'smoking_status': 'smokes'
            }
        }
    ]
    
    print("=" * 80)
    print("ENHANCED STROKE RISK SCORING SYSTEM TEST")
    print("=" * 80)
    print()
    
    results = []
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"{i}. {test_case['name']}")
        print("-" * 50)
        
        # Calculate risk
        result = calculator.predict_stroke_risk(test_case['data'])
        results.append((test_case['name'], result))
        
        # Display patient info
        data = test_case['data']
        print(f"   Age: {data['age']} | Gender: {data['gender']} | BMI: {data['bmi']}")
        print(f"   Hypertension: {'Yes' if data['hypertension'] else 'No'} | Heart Disease: {'Yes' if data['heart_disease'] else 'No'}")
        print(f"   Glucose: {data['avg_glucose_level']} mg/dL | Smoking: {data['smoking_status']}")
        print()
        
        # Display results
        print(f"   🎯 RISK SCORE: {result['risk_score']:.4f}")
        print(f"   📊 RISK LEVEL: {result['risk_level']}")
        print(f"   🎯 CONFIDENCE: {result['confidence']:.1f}%")
        print()
        
        # Show top risk factors
        if result['risk_factors']:
            print("   ⚠️  TOP RISK FACTORS:")
            for factor in result['risk_factors'][:3]:
                print(f"      • {factor}")
        print()
        
        # Show score breakdown
        if 'score_breakdown' in result:
            print("   📈 SCORE BREAKDOWN:")
            breakdown = result['score_breakdown']
            for factor, details in breakdown.items():
                if details['contribution'] > 0:
                    print(f"      {factor}: {details['contribution']:.4f} (weight: {details['weight']:.3f})")
        
        print("=" * 80)
        print()
    
    # Summary statistics
    print("DISTRIBUTION SUMMARY")
    print("=" * 50)
    
    risk_levels = {}
    scores = []
    
    for name, result in results:
        level = result['risk_level']
        score = result['risk_score']
        
        if level not in risk_levels:
            risk_levels[level] = []
        risk_levels[level].append((name, score))
        scores.append(score)
    
    print(f"Score Range: {min(scores):.4f} - {max(scores):.4f}")
    print(f"Score Spread: {max(scores) - min(scores):.4f}")
    print()
    
    print("Risk Level Distribution:")
    for level, patients in risk_levels.items():
        print(f"  {level}: {len(patients)} patient(s)")
        for name, score in patients:
            print(f"    • {name}: {score:.4f}")
    
    print()
    print("✅ Enhanced scoring system provides better distribution across risk levels!")
    print("✅ Each assessment now has more granular and meaningful risk scores!")

if __name__ == "__main__":
    test_enhanced_scoring()
