# Process all bills, or bills that need processed, determine their bag-of-words, and save it in the database.
# We store two things:
# 1. A set of vectors for each word to the dictionary: [(0, 1), (1, 1)]
# 2. A TF-IDF model: [(5, 0.5898341626740045), (11, 0.8075244024440723)]
# This requires the dictionary to be created first.
