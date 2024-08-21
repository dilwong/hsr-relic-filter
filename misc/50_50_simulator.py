import random

def simulate_trials():
    n = random.randint(2, 100)  # Random number of trials between 2 and 20
    results = ""
    win_follows_win = 0
    loss_follows_win = 0
    lost = False
    
    for _ in range(n):
        if not lost:
            if random.random() < 0.5:  # 50% chance of winning initially
                results += "W"
            else:
                lost = True
                if random.random() < 1/8:  # 1/8 chance of winning after losing
                    results += "W"
                else:
                    results += "L"
        else:
            results += "W"
            lost = False  # Reset the 'lost' attribute
    
    # Count the number of times a W follows a W and an L follows a W
    for i in range(len(results) - 1):
        if results[i] == "W" and results[i + 1] == "W":
            win_follows_win += 1
        elif results[i] == "W" and results[i + 1] == "L":
            loss_follows_win += 1
    
    return results, win_follows_win, loss_follows_win

# Perform m trials
m = 1_000_000
total_win_follows_win = 0
total_loss_follows_win = 0
total_wins = 0
total_losses = 0
results_list = []

for _ in range(m):
    results, win_follows_win, loss_follows_win = simulate_trials()
    results_list.append(results)
    total_win_follows_win += win_follows_win
    total_loss_follows_win += loss_follows_win
    total_wins += results.count('W')
    total_losses += results.count('L')

# Calculate the ratios
total_ratio_1 = total_win_follows_win / (total_win_follows_win + total_loss_follows_win)
total_ratio_2 = total_wins / (total_wins + total_losses)

print("Total win_follows_win / (win_follows_win + loss_follows_wins) ratio:", total_ratio_1)
print("Total W/(L+W) ratio:", total_ratio_2)

# Print the list of 'W'/'L' strings
print("List of 'W'/'L' strings (first 10):")
for i in range(10):
    print(results_list[i])
