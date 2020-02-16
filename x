def binaryPatternMatching(pattern, s):
    count = 0
    vowels = set(['a','e','i','o','u','y'])
    if len(s) > len(pattern):
        window = []
        for i in range(0,len(s)):
            window.append(s[i])
            if(len(window) == len(pattern)):
                print(window)
                match = True
                for j in range(0,len(pattern)):
                    if window[j] in vowels and (pattern[j] == ""):

                    elif window[j] not in vowels and (pattern[j] == "1"):
                        count+=1

                window.pop(0)
    elif len(s) == len(pattern):
        for j in range(0,len(pattern)):
            if s[j] in vowels and pattern[j] == "0":
                count+=1
            elif s[j] not in vowels and (pattern[j] == 1):
                count+=1
    return count