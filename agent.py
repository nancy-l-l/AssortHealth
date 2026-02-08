from typing import Dict, Any, Optional, List
from llm import LLM
from validators import parse_dob, validate_address_google
from data import PROVIDERS, SLOTS

STEPS = [
    'full_name',
    'dob',
    'payer_name',
    'address',
    'insurance_id',
    'cheif_complaint',
    'appointment',
    'confirm',
]

def empty_state() -> Dict[str, Any]:
    return {
       'patient': {'full_name': None, 'dob': None},
       'insurance': {'payer_name': None, 'insurance_id': None},
       'medical': {'chief_complaint': None},
       'demographics': {'address': {'street': None, 'city': None, 'state': None, 'zip': None}},
         'appointment': {'provider_id': None, 'slot_id': None},
    }
class IntakeAgent:
    def __init__(self, model:str='gpt-5.2'):
        self.llm = LLM(model=model)
        self.state = empty_state()
        self.step = 'full_name'
    
    def run(self):
        print("Welcome to the patient intake system. Let's get started!")
        while True:
            user = input("\nYou: ").strip()
            if user.lower() in {'quit', 'exit'}:
                print("Goodbye!")
                return
            assistant_msg = self.handle_turn(user)
            print(f"Assistant: {assistant_msg}")
            
            if self.step == 'done':
                return
            
    def handle_turn(self, user_msg:str) -> str:
       if self.step == 'appointment':
           return self._handle_appointment(user_msg)
       
       if self.step == 'confirm':
           if user_msg.lower() in {'yes', 'y', 'confirm', 'confirmed', 'looks good'}:
               self.step = 'done'
               return 'Great! Your appointment is confirmed. See you then!'
           
           if user_msg.lower() in {'no', 'n', 'change', 'edit'}:
               self.step = 'full_name'
               self.state = empty_state()
               return 'Okay, let\'s start over. What is your full name?'
           
           return 'Please respond with "yes" to confirm or "no" to start over.'
    
       system_prompt = self._system_prompt_for_step()
       parsed = self.llm.extract_and_respond(system_prompt, user_msg)
       
       
       extracted = parsed.get('extracted', {}) or {}
       msg = self._apply_extracted(extracted)
       #print("DEBUG parsed:", parsed)
       #print("DEBUG extracted:", extracted)
       if msg:
           return msg
       self._advance_step()
       return self._question_for_step()
    def _system_prompt_for_step(self) -> str:
        return f"""You are a helpful assistant for collecting patient intake information. The current step is '{self.step}'. Current collected state is: {self.state}.
        your job:
        1) Extract relevant information from the user's message that pertains to the current step.
        2) Extract relevant fields into 'extracted' using these keys when present:
        - patient.full_name
        - patient.dob
        - insurance.payer_name
        - insurance.insurance_id
        - medical.chief_complaint
        - demographics.address.street / city / state / zip
        3) If the extracted information is sufficient to fill the current step, include in the corresponding field.
        4) If the extracted information is not sufficient, leave the field as None and respond with a follow up question to get the missing information.
        5) If the current step is 'confirm', respond with a summary of the collected information and ask the user to confirm if it's correct.
        6) Return STRICT JSON only. """.strip()
        
    def _apply_extracted(self, extracted:Dict[str, Any]) -> Optional[str]:
        def get(path: str):
            cur = extracted
            for p in path.split('.'):
                if not isinstance(cur, dict) or p not in cur:
                    return None
                cur = cur[p]
            return cur
        
        name = get('patient.full_name')
        if name and not self.state['patient']['full_name']:
            self.state['patient']['full_name'] = str(name).strip()
            
        import re

        dob_raw = get('patient.dob') or extracted.get('patient.dob')
        if dob_raw and not self.state['patient']['dob']:
            s = str(dob_raw).strip()

            # if model returns ISO YYYY-MM-DD, convert to MM/DD/YYYY
            m = re.match(r"^(\d{4})-(\d{2})-(\d{2})$", s)
            if m:
                y, mo, d = m.group(1), m.group(2), m.group(3)
                s = f"{mo}/{d}/{y}"

            dob = parse_dob(s)
            if dob:
                self.state['patient']['dob'] = dob

        if dob_raw and not self.state['patient']['dob']:
            dob = parse_dob(str(dob_raw))
            if dob:
                self.state['patient']['dob'] = dob
                
        payer = get('insurance.payer_name')
        if payer and not self.state['insurance']['payer_name']:
            self.state['insurance']['payer_name'] = str(payer).strip()
        
        ins_id = get('insurance.insurance_id')
        if ins_id and not self.state['insurance']['insurance_id']:
            self.state['insurance']['insurance_id'] = str(ins_id).strip()
        
        cc = get('medical.chief_complaint')
        if cc and not self.state['medical']['chief_complaint']:
            self.state['medical']['chief_complaint'] = str(cc).strip()
        
        addr = get('demographics.address')
        if isinstance(addr, dict):
            for field in ['street', 'city', 'state', 'zip']:
                val = addr.get(field)
                if val and not self.state['demographics']['address'][field]:
                    self.state['demographics']['address'][field] = str(val).strip()
        
        if self.step == 'full_name':
            if not self.state['patient']['full_name']:
                return "Could you please provide your full name?"
            return None
        if self.step == 'dob':
            if not self.state['patient']['dob']:
                return "Could you please provide your date of birth? (e.g. MM/DD/YYYY)"
            return None

        '''
            if not self.state['patient']['dob']:
                return "Could you please provide your date of birth? (e.g. MM/DD/YYYY)"
            return None
        '''
        if self.step == 'payer_name':
            if not self.state['insurance']['payer_name']:
                return "Could you please provide the name of your insurance provider?"
            return None
        if self.step == 'insurance_id':
            if ins_id is None and extracted.get('intent', {}).get('skip_insurance_id'):
                self.state['insurance']['insurance_id'] = None
            return None
        if self.step == 'chief_complaint':
            if not self.state['medical']['chief_complaint']:
                return "Could you please briefly describe your chief medical complaint or reason for the visit?"
            return None
        if self.step == 'address':
            addr_state = self.state['demographics']['address']
            if not all(addr_state.values()):
                missing = [k for k, v in addr_state.items() if not v]
                return f"Could you please provide your address? Missing fields: {', '.join(missing)}"
            is_valid, msg, normalized = validate_address_google(addr_state)
            if is_valid:
                self.state['demographics']['address'] = normalized
                return None
            return msg
        return None
    
    def _advance_step(self):
        i = STEPS.index(self.step)
        self.step = STEPS[i+1]
    def _question_for_step(self) -> str:
        if self.step == 'dob':
            return "What is your date of birth? (e.g. MM/DD/YYYY)"
        if self.step == 'payer_name':
            return "What is the name of your insurance provider?"
        if self.step == 'insurance_id':
            return "What is your insurance ID number? If you don't have it, you can say 'I don't know' or 'I will provide it later'."
        if self.step == 'chief_complaint':
            return "What is the main reason for your visit today? Please briefly describe your symptoms or concerns."
        if self.step == 'address':
            return "What is your home address? Please include street, city, state, and zip code."
        if self.step == 'appointment':
            return self._appointment_menu()
        if self.step == 'confirm':
           return self._confirmation_prompt()
        return "Okay."
    
    def _appointment_menu(self) -> str:
        lines = ['Here are the available appointment slots with our providers:']
        for idx, p in enumerate(PROVIDERS):
            lines.append(f"{p.name} -- ({p.specialty}):")
            for s in SLOTS:
                if s.provider_id == p.id:   
                    lines.append(f"  - {s.start_iso} (slot id: {s.id})")
        lines.append("")
        lines.append("Please select a slot by providing the slot id (e.g. 's2').")
        return '\n'.join(lines)
    
    def _handle_appointment(self, user_msg:str) -> str:
        choice = user_msg.strip().lower()
        if choice in {'menu', 'list'}:
            return self._appointment_menu()
        # accept direct slot id like "s2"
        slot = next((s for s in SLOTS if s.id.lower() == choice), None)
        if slot:
            provider = next((p for p in PROVIDERS if p.id == slot.provider_id), None)
            self.state['appointment']['provider_id'] = provider.id if provider else slot.provider_id
            self.state['appointment']['slot_id'] = slot.id
            self.step = 'confirm'
            return self._confirmation_prompt()

        if '.' in choice:
            a, b = choice.split('.', 1)
            if a.isdigit() and b.isdigit():
                pi = int(a) - 1
                sj = int(b) - 1
                if 0 <= pi < len(PROVIDERS):
                    provider = PROVIDERS[pi]
                    provider_slots = [s for s in SLOTS if s.provider_id == provider.id]
                    if 0 <= sj < len(provider_slots):
                        slot = provider_slots[sj]
                        self.state['appointment']['provider_id'] = provider.id
                        self.state['appointment']['slot_id'] = slot.id
                        self.step = 'confirm'
                        return self._confirmation_prompt()
        return "Sorry, I didn't understand that. Please select a slot by providing the slot id (e.g. 's2'), or type 'menu' to see the options again."
    def _confirmation_prompt(self) -> str:
        provider = next((p for p in PROVIDERS if p.id == self.state['appointment']['provider_id']), None)
        slot = next((s for s in SLOTS if s.id == self.state['appointment']['slot_id']), None)
        addr = self.state['demographics']['address']
        
        summary = f"""Awesome! Here is the information I have collected:\n\n
            Appointment with: {provider.name if provider else 'N/A'} ({provider.specialty if provider else 'N/A'})\n
            Appointment time: {slot.start_iso if slot else 'N/A'}\n
            Patient name: {self.state['patient']['full_name']}\n
            Date of Birth: {self.state['patient']['dob']}\n
            Insurance Provider: {self.state['insurance']['payer_name']}\n
            Address: {addr['street']}, {addr['city']}, {addr['state']} {addr['zip']}\n
            
        Please confirm if all this information is correct. (yes/no)
        """.strip()
        return summary