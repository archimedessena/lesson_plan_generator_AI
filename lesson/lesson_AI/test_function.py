def average_score(scores):
    if len(scores) == 0:
        return None
    else:
        return sum(scores) / len(scores)
    
    
def use_result():
    if average_score(scores) > 0:
        print("You are above average.")
    else:
        print("You need help")
        
        
scores = [-1, -2, -3, -4, 5]
average_score(scores)
#print(use_result())




def calculate_grade(score):
    if score >= 70:
        return "A"
    elif score >= 50:
        return "B"
    return "C"


def generate_comment(score):
    if score >= 70:
        return "Excellent performance"
    elif score >= 50:
        return "Good effort"
    return "Needs improvement"


def build_report(name, score):
    return {
        "name": name,
        "score": score,
        "grade": calculate_grade(score),
        "comment": generate_comment(score)
    }
    
    
    
    
report = build_report("Alice", 85)
print(report)