import json
import datetime
import csv

def get_team_members(fname):
    with open(fname) as f:
        lines = [line.rstrip() for line in f]
    return lines

def get_customer_task_time(fname):
    with open(fname) as jf:
        data = json.load(jf)
    return data

def get_total_h_tasks(customer_task_time):
    sum = 0
    for c in customer_task_time:
        sum += customer_task_time[c]
    return sum

def get_available_slot_sizes(n_team_members, total_h_tasks):
    max_h_slot_size = 5 # h
    slot_size = 0
    runs = []
    for n_active_team_members in range(n_team_members, 0, -1):
        available_slots = []
        for slot_size in range(1, max_h_slot_size):
            if total_h_tasks % slot_size == 0 and n_active_team_members * slot_size == total_h_tasks:
                available_slots.append(slot_size)
        if len(available_slots) > 0:
            n_off = n_team_members - n_active_team_members
            runs.append([available_slots, n_active_team_members, n_off])
    return runs # [[list of possible slot sizes], n members doing TH that week, n members not doing TH that week]

def get_best_slot_setup(available_slot_sizes):
    # Find optimal setup, which is when lowest h / w / slot
    lowest_seen = 100
    options_idx = 0
    new_options = []
    for options in available_slot_sizes:
        for slot_size in options[0]:
            if slot_size == lowest_seen:
                new_options.append(options_idx)
            elif slot_size < lowest_seen:
                lowest_seen = slot_size
                new_options.append(options_idx)
        options_idx += 1
    if len(new_options) == 1:
        # By definition there is only 1 slot size => flatten slot size list
        new_lst = []
        new_lst.append(available_slot_sizes[new_options[0]][0][0])
        new_lst = new_lst + available_slot_sizes[new_options[0]][1:]
        return new_lst
    else:
        # When we have same optimal low h / w but different setup with active / inactive.
        # The optimal choice would be lowest active
        lowest_seen = 100
        option_idx = 0
        for option in new_options:
            for active_size in available_slot_sizes[option][1]:
                if active_size < lowest_seen:
                    lowest_seen = active_size
                    best_option_idx = option_idx
            option_idx += 1
        return available_slot_sizes[best_option_idx]

def get_customer_assigned_slots(setup, customer_task_time):
    output = {}
    # Generate output json skeleton
    for n_slot in range(1, setup[1]+1):
        output['slot_%s'%n_slot] = {'assigned_member': []}
        output['slot_%s'%n_slot]['customers'] = {}
    # Assign customers to slots
    slot_size = setup[0]
    for i in range(0, len(output)):
        for customer, h in customer_task_time.items():
            if customer_task_time[customer] > 0:
                # If the current set of customers in slot is at capacity => skip this customer
                if sum(list(output['slot_%s'%str(i+1)]['customers'].values())) >= slot_size:
                    continue
                else:
                    # If the customer we are trying to add has more hours than slot capacity => split it over multiple slots
                    if h > slot_size:
                        output['slot_%s'%str(i+1)]['customers'][customer] = (h - slot_size)
                        customer_task_time[customer] -= (h - slot_size)
                    else:
                        output['slot_%s'%str(i+1)]['customers'][customer] = h
                        customer_task_time[customer] -= h
            else:
                continue
    return output

def get_team_assigned_slots(setup, team_members, slot_setup):
    count = 0
    drift_quotient = 1
    while count < len(slot_setup): # n slots
        if drift_quotient >= 1:
            for member in team_members:
                slot_setup['slot_%s'%str(count+1)]['assigned_member'].append(member)
            drift_quotient -= 1
            count += 1
        else:
            drift_quotient += len(slot_setup) / (len(team_members) - len(slot_setup))
        # rotate team_members
        team_members.append(team_members[0])
        team_members.pop(0)
    return slot_setup

def write_json_file(fname, data):
    with open(fname, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_csv_format(inpt, start_week_number):
    csv_rows = []
    # Make header
    row = ['Customers', 'Hours/Week']
    for week_nr in range(start_week_number, len(inpt['slot_1']['assigned_member'])+start_week_number): # same length all slots
        row.append('W%02d'%week_nr,)
    csv_rows.append(row)
    # Add data
    for row_idx in range(len(inpt)):
        row = []
        slot_customer_combo = ' + '.join(list(inpt['slot_%s'%str(row_idx+1)]['customers'].keys())) # format for column 1 value
        row.append(slot_customer_combo)
        slot_hour_combo = ' + '.join([str(v) for v in list(inpt['slot_%s'%str(row_idx+1)]['customers'].values())])
        row.append(slot_hour_combo)
        for member in inpt['slot_%s'%str(row_idx+1)]['assigned_member']: # same length all slots
            row.append(member)
        csv_rows.append(row)
    return csv_rows

def get_current_week_number():
    date_now = datetime.date.today()
    _, week_number, _ = date_now.isocalendar()
    return week_number

def write_csv_file(fname, data):
    with open(fname, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerows(data)

def get_html_table(data):
    # Header
    s_thead_inner = ''
    for i in range(len(data[0])):
        s_thead_inner += '<th style="text-align: left;"><p>%s</p></th>'%data[0][i]
    s_thead = '<thead><tr>%s</tr></thead>'%s_thead_inner
    # Body
    s_tbody_inner =''
    checkmark_id_inc = 1000
    for row_idx in range(1, len(data)):
        s_row = ''
        for col_idx in range(len(data[row_idx])):
            if col_idx < 2: # First two columns to not have checkbox
                s_row += '<th style="text-align: left;">%s</th>'%data[row_idx][col_idx]
            else:
                checkmark_id_inc += 1
                s_row += '<td style="text-align: left;"><ac:task-list><ac:task><ac:task-id>%s</ac:task-id><ac:task-status>incomplete</ac:task-status><ac:task-body>%s</ac:task-body></ac:task></ac:task-list></td>'%(checkmark_id_inc, data[row_idx][col_idx])
        s_tbody_inner += '<tr>%s</tr>'%s_row
    s_tbody = '<tbody>%s</tbody>'%s_tbody_inner
    output = '<table class="relative-table wrapped" style="width: 100%%">%s%s</table>'%(s_thead, s_tbody)
    return output

def write_html_file(fname, data):
    # HTML prettyprinted with BeautifulSoup
    from bs4 import BeautifulSoup as bs
    with open(fname, 'w') as f:
        f.write(bs(data, features='html.parser').prettify())

def main():
    team_members_fname = 'team_members.txt'
    print('\n[+] Reading team member data <= input/%s'%team_members_fname)
    team_members = get_team_members('input/%s'%team_members_fname) # member\nmember\nmember

    customer_task_time_fname = 'customer_task_time.json'
    print('[+] Reading customer data <= input/%s'%customer_task_time_fname)
    customer_task_time = get_customer_task_time('input/%s'%customer_task_time_fname) # {"cname": h, "cname": h}
    total_h_tasks = get_total_h_tasks(customer_task_time) # Total hours of TH work / week
    start_week_number = get_current_week_number() # Start from the current week the script is ran

    # Find optimal setup slot h / member, n active members and n inactive members, n total slots
    print('[+] Looking for optimal setup...')
    available_slot_sizes = get_available_slot_sizes(len(team_members), total_h_tasks) # Brute force possible slot sizes
    best_slot_setup = get_best_slot_setup(available_slot_sizes) # Best = lowest h / w / member, O = [h slot size, n active, n inactive]
    print('[+] Optimal setup found:\n\tSlot Size: %s Hours / Member | Active Members (slots): %s | Inactive Members (slots): %s | Total slots: %s' % (best_slot_setup[0], best_slot_setup[1], best_slot_setup[2], best_slot_setup[1]+best_slot_setup[2]))
    
    # Assign customers to slots => {slot_1: {assigned_member: [member week 1, member week 2], customers: {customer_1: h, customer_2: h}}, slot_2: {assigned_member = [member week 1, member week 2], customers: {customer_2: h, customer_3: h}}}
    customer_assigned_slots = get_customer_assigned_slots(best_slot_setup, customer_task_time)

    # Assign team members to slots
    team_assigned_slots = get_team_assigned_slots(best_slot_setup, team_members, customer_assigned_slots)

    # Dump the data to json file
    json_fname = 'output.json'
    print('[+] Writing JSON data => output/%s'%json_fname)
    write_json_file('output/%s'%json_fname, team_assigned_slots)
    
    # Format csv data
    csv_output = get_csv_format(team_assigned_slots, start_week_number)

    # Dump data to csv file
    csv_fname = 'output.csv'
    print('[+] Writing CSV data => output/%s'%csv_fname)
    write_csv_file('output/%s'%csv_fname, csv_output)

    # Convert csv data to HTML table (confluence table)
    html_table = get_html_table(csv_output)

    # Dump data to HTML file
    html_fname = 'output.html'
    print('[+] Writing HTML data => output/%s'%html_fname)
    write_html_file('output/%s'%html_fname, html_table)

if __name__ == '__main__':
    main()