import os
import json
import re

#%%
def get_passcode(pc_name):
    ''' Get passcode for remote PCs from json
    '''
    with open(os.path.dirname(os.path.abspath(__file__)) + '\passcode.json') as f:
        passcode = json.load(f)
        
    return passcode[pc_name]


# Define the canonical names
canonical_names = [
    'Kanghoon Jung',
    'Kenta Hagihara',
    'Xinxin Yin',
    'Bowen Tan',
    'Galen Lynch',
    'Yoni Browning',
    'Anna Lakunina',
    'Tiffany Ona',
    'Sue Su',
    'Smrithi Sunil',
    'Linda Amarante'
]

# Define corrections for typos or variations
corrections = {
    'Sue Sue': 'Sue Su'  # Add other corrections if needed
}

def reformat_PI_names(entry):
    individual_users = [u.strip() for u in entry.split(',')]
    processed_names = []
    for user in individual_users:
        # Extract name from "Name <email>" format
        match = re.match(r'^(.*?)\s*<[^>]+>$', user)
        if match:
            name = match.group(1).strip()
        else:
            # Process email-only entries
            if '@' in user:
                local_part = user.split('@')[0]
                parts = local_part.split('.')
                name_parts = [part.capitalize() for part in parts]
                name = ' '.join(name_parts)
            else:
                name = user.strip()
        # Apply corrections
        name = corrections.get(name, name)
        # Check against canonical names
        if name in canonical_names:
            processed_names.append(name)
        else:
            processed_names.append(name)  # Optionally handle unrecognized names
    return ', '.join(processed_names)