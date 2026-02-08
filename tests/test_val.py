from validators import parse_dob

def test_parse_dob():
    assert parse_dob('01/31/2002') == '2002-01-31'
    
def test_parse_dob_textual():
    assert parse_dob('January 5, 1999') == '1999-01-05'
   
def test_dob_out_of_range():
    assert parse_dob('01/01/1800') is None
    assert parse_dob('01/01/3000') is None