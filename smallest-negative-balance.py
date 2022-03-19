# Smallest Negative Balance

# You are working on a new application for recording debts. This program allows users to create groups
# that show all records of debts between the group members. Given the group debt, records (including the
# borrower name, lender name, and debt amount), who in the group has the smallest negative balance?

# Notes:
# -10 is smaller than -1.
# if multiple people have the smallest negative balance, return the list in alphabetical order.
# if nobody has a negative balance, return the string "Nobody has a negative balance"

# Example:
# n = 6
# debts = ['Alex Blake 2', 'Blake Alex 2', 'Casey Alex 5', 'Blake Casey 7', 'Alex Blake 4', 'Alex Casey 4']

# There are 6 debt records as shown in the table below:
# | borrower    |   lender  |   ammount |
# | Alex        |   Blake   |   2       |
# | Blake       |   Alex    |   2       |
# | Casey       |   Alex    |   5       |
# | Blake       |   Casey   |   7       |
# | Alex        |   Blake   |   4       |
# | Alex        |   Casey   |   4       |

# Returns
# string[]: an array of strings denoting an alphabetically ordered list of members with the smallest negative
# balance, or an array containing the string "Nobody has a negative balance"

# Contraints
# 1 =< n =< 2 x 10^5
# debts[i][2] represents an integer between 1 and 1000 inclusively.
# 1 =< length of debts[i][0], length of debts[i][1] =< 20
# The first character of debts[i][0] and debts[i][1] is capital English letter
# Every character of debts[i][j] and debts[i][1] except the first one is lowercase English letter.
# debts[i][0] != debts[i][1]

# Input format for custom testing
# The first line contains an integer, n, the number of rows in debts
# The second line contains an integer, 3, the number of elements in debts[i]
# Each line i of the n subsequent lines (where 0 =< i =< n) contains 3 space-separated strings:
#   debts[i][0], debts[i][1], debts[i][2], borrow, lender, amount.

def split_group(record):
    value = record.split(' ')
    borrower,lender,amount = value[0].upper(),value[1].upper(),int(value[2])
    return [borrower,lender,amount]

def calculate_debts(record,group_debts):
    borrower,lender,amount = record[0],record[1],record[2]
    
    if borrower in group_debts:
        borrow_amount = group_debts.get(borrower) - amount
    else:
        borrow_amount = -amount
        
    group_debts[borrower] = borrow_amount
        
    if lender in group_debts:
        lender_amount = group_debts.get(lender) + amount
    else:
        lender_amount = amount
        
    group_debts[lender] = lender_amount
    
    return group_debts

def get_smallest_balance(group_debts):
    minval = min(group_debts.values())
    res = []
    if minval < 0:
        res = list(filter(lambda x: group_debts[x]==minval, group_debts))
    return res

def smallest_negative_balance(debts):
    group_debts = dict()
    for record in debts:
        group = split_group(record)
        members_debt = calculate_debts(group, group_debts)

    members_smallest_balance = get_smallest_balance(members_debt)
    
    if members_smallest_balance:
        members_smallest_balance.sort()
    else:
       members_smallest_balance = ['Nobody has a negative balance']
    
    return members_smallest_balance
           
if __name__ == '__main__':
    
    debs_table = ['Alex Blake 2', 'Blake Alex 2', 'Casey Alex 5', 'Blake Casey 7', 'Alex Blake 4', 'Alex Casey 4']
    print(smallest_negative_balance(debs_table))