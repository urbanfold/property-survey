"""Build the printable Urbanfold client guide (optional dependency: reportlab).
Uses Open Sans fonts installed under /usr/share/fonts/truetype/open-sans.
Run from the repository: python scripts/build_survey_guide.py
"""
from pathlib import Path
import math
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Flowable, KeepTogether
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import A4

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'documents/Urbanfold_Self_Survey_Guide.pdf'
APP='https://urbanfold.github.io/property-survey/'
FONT=Path('/usr/share/fonts/truetype/open-sans')
for name,filename in [('OpenSans','OpenSans-Regular.ttf'),('OpenSans-Bold','OpenSans-Semibold.ttf'),('OpenSans-Italic','OpenSans-Italic.ttf')]:
    pdfmetrics.registerFont(TTFont(name,str(FONT/filename)))
pdfmetrics.registerFontFamily('OpenSans',normal='OpenSans',bold='OpenSans-Bold',italic='OpenSans-Italic',boldItalic='OpenSans-Bold')
INK=colors.HexColor('#344349'); MUTED=colors.HexColor('#66777e'); BLUE=colors.HexColor('#789eac'); PALE=colors.HexColor('#eef4f6'); LINE=colors.HexColor('#d8e3e8'); ACCENT=colors.HexColor('#2563eb')
W,H=A4; CW=W-88
styles={
 'body':ParagraphStyle('body',fontName='OpenSans',fontSize=10,leading=15,textColor=INK,spaceAfter=7),
 'small':ParagraphStyle('small',fontName='OpenSans',fontSize=8.5,leading=12.5,textColor=MUTED,spaceAfter=5),
 'h1':ParagraphStyle('h1',fontName='OpenSans-Bold',fontSize=25,leading=31,textColor=INK,spaceAfter=10),
 'h2':ParagraphStyle('h2',fontName='OpenSans-Bold',fontSize=13,leading=18,textColor=INK,spaceBefore=12,spaceAfter=6,keepWithNext=True),
 'intro':ParagraphStyle('intro',fontName='OpenSans',fontSize=11,leading=17,textColor=MUTED,spaceAfter=12),
 'tag':ParagraphStyle('tag',fontName='OpenSans-Bold',fontSize=9,leading=13,textColor=BLUE,spaceAfter=6),
 'box':ParagraphStyle('box',fontName='OpenSans',fontSize=9.5,leading=14.5,textColor=INK),
 'bullet':ParagraphStyle('bullet',fontName='OpenSans',fontSize=10,leading=15,textColor=INK,leftIndent=12,firstLineIndent=-11,spaceAfter=4),
}
def P(text,kind='body'):return Paragraph(text,styles[kind])
def bullet(text):return P('• '+text,'bullet')
def box(title,text):
    t=Table([[P('<b>'+title+'</b><br/>'+text,'box')]],colWidths=[CW])
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,-1),PALE),('BOX',(0,0),(-1,-1),.5,LINE),('LEFTPADDING',(0,0),(-1,-1),12),('RIGHTPADDING',(0,0),(-1,-1),12),('TOPPADDING',(0,0),(-1,-1),10),('BOTTOMPADDING',(0,0),(-1,-1),10)]))
    return t

def page(c,doc):
    c.saveState()
    c.setFillColor(INK);c.setFont('OpenSans-Bold',14);c.drawString(44,H-38,'URBANFOLD')
    c.setFillColor(MUTED);c.setFont('OpenSans',7.5);c.drawRightString(W-44,H-37,'CLIENT SELF-SURVEY GUIDE')
    c.setStrokeColor(LINE);c.setLineWidth(.6);c.line(44,H-50,W-44,H-50)
    c.line(44,44,W-44,44)
    c.setFont('OpenSans',7.5);c.setFillColor(MUTED)
    c.drawString(44,30,'survey@urbanfold.uk')
    c.linkURL('mailto:survey@urbanfold.uk',(44,26,170,39),relative=0,thickness=0)
    c.drawCentredString(W/2,30,'Client guide • October 2026')
    c.drawRightString(W-44,30,f'{doc.page} / 4')
    c.restoreState()

class FloorPlan(Flowable):
    def __init__(self):super().__init__();self.width=CW;self.height=263
    def draw(self):
        c=self.canv;c.saveState()
        c.setFillColor(PALE);c.roundRect(0,0,CW,self.height,8,fill=1,stroke=0)
        c.setFont('OpenSans-Bold',9);c.setFillColor(INK);c.drawString(14,245,'EXAMPLE: GROUND FLOOR')
        c.setFont('OpenSans',8);c.setFillColor(MUTED);c.drawRightString(CW-14,245,'Illustrative only • not to scale')
        x=90;y=45;ww=300;hh=165;mid=x+145;hy=y+80
        c.setFillColor(colors.white);c.rect(x,y,ww,hh,fill=1,stroke=0)
        c.setStrokeColor(INK);c.setLineWidth(3.2);c.rect(x,y,ww,hh,fill=0,stroke=1)
        c.line(mid,y,mid,y+hh);c.line(x,hy,x+ww,hy)
        def gap(a,b):
            c.setStrokeColor(colors.white);c.setLineWidth(6);c.line(*a,*b)
        def window(a,b):
            gap(a,b);c.setStrokeColor(BLUE);c.setLineWidth(1.2)
            if a[1]==b[1]:
                for d in [-2,2]:c.line(a[0],a[1]+d,b[0],b[1]+d)
                c.line(a[0],a[1]-3,a[0],a[1]+3);c.line(b[0],b[1]-3,b[0],b[1]+3)
            else:
                for d in [-2,2]:c.line(a[0]+d,a[1],b[0]+d,b[1])
                c.line(a[0]-3,a[1],a[0]+3,a[1]);c.line(b[0]-3,b[1],b[0]+3,b[1])
        window((x+25,y),(x+85,y));window((x+25,y+hh),(x+85,y+hh));window((x+ww,y+105),(x+ww,y+143))
        # Doors: leave a wall opening and draw an angled leaf into the room.
        gap((mid,y+22),(mid,y+50));c.setStrokeColor(INK);c.setLineWidth(1.1);c.line(mid,y+22,mid-24,y+39)
        gap((x+48,hy),(x+76,hy));c.setStrokeColor(INK);c.setLineWidth(1.1);c.line(x+48,hy,x+65,hy-24)
        gap((mid+55,hy),(mid+83,hy));c.setStrokeColor(INK);c.setLineWidth(1.1);c.line(mid+55,hy,mid+72,hy+24)
        gap((mid+55,y),(mid+83,y));c.setStrokeColor(INK);c.setLineWidth(1.1);c.line(mid+55,y,mid+72,y+24)
        # A small chimney breast and stairs make useful position references.
        c.setStrokeColor(INK);c.setFillColor(LINE);c.rect(x,y+25,10,29,fill=1,stroke=1)
        c.setLineWidth(.5)
        for i in range(7):c.line(x+ww-32,y+9+i*7,x+ww-8,y+9+i*7)
        c.line(x+ww-32,y+9,x+ww-32,y+51);c.line(x+ww-8,y+9,x+ww-8,y+51)
        c.setFont('OpenSans-Bold',9);c.setFillColor(INK)
        c.drawCentredString(x+75,y+hh-41,'Dining room')
        c.drawCentredString(x+75,y+40,'Living room')
        c.drawCentredString(mid+73,y+hh-41,'Kitchen')
        c.drawCentredString(mid+62,y+58,'Hall / stairs')
        c.setFont('OpenSans',7.7);c.setFillColor(MUTED);c.drawCentredString(x+ww/2,y-14,'FRONT OF HOUSE / ENTRANCE')
        c.drawString(17,198,'REAR');c.drawString(17,187,'OF HOUSE')
        # Common house-based axes prevent room dimensions being swapped.
        def double_arrow(x1,y1,x2,y2):
            c.setStrokeColor(BLUE);c.setLineWidth(.8);c.line(x1,y1,x2,y2)
            angle=math.atan2(y2-y1,x2-x1)
            for xx,yy,aa in [(x1,y1,angle),(x2,y2,angle+math.pi)]:
                for side in [-.45,.45]:
                    c.line(xx,yy,xx+5*math.cos(aa+side),yy+5*math.sin(aa+side))
        double_arrow(x,y+hh+10,x+ww,y+hh+10)
        c.setFont('OpenSans-Bold',7.5);c.setFillColor(INK)
        c.drawCentredString(x+ww/2,y+hh+17,'WIDTH: parallel to the front of the house')
        double_arrow(x+ww+20,y,x+ww+20,y+hh)
        c.saveState();c.translate(x+ww+34,y+12);c.rotate(90)
        c.drawString(0,0,'LENGTH: front to back, at 90° to the front')
        c.restoreState()
        c.setStrokeColor(BLUE);c.setLineWidth(1.2);c.line(17,17,42,17);c.line(17,21,42,21)
        c.setFillColor(MUTED);c.setFont('OpenSans',7.5);c.drawString(48,16,'Window')
        c.setStrokeColor(INK);c.line(128,15,151,28);c.drawString(159,16,'Angled line shows how a door opens')
        c.restoreState()

story=[]
def add(*items):story.extend(items)
def heading(step,title):add(P(f'{step}  /  {title}','h2'))

# Page one: the preparation needed before opening the app.
add(P('BEFORE YOU START','tag'),P('A simple survey.<br/>A clearer design brief.','h1'),P('Use this guide to record your home and explain your proposal, one step at a time. You do not need drawing experience.','intro'))
add(P('Prepare a sketch of every floor','h2'),P('Using pen or pencil, draw a simple layout for each floor level. Focus on where rooms sit in relation to one another; a neat outline is enough.'))
for text in [
 'Label each floor and every room, including hallways, landings and stairs.',
 'Mark windows and door openings. Add an angled line from each door hinge to show which way the door opens.',
 'Label the front and rear of the house. Mark the width and length directions, and where you would like the extension or other proposed work.',
 'You do not need a detailed or perfectly scaled drawing. Photograph each finished sketch clearly.'
]:add(bullet(text))
add(Spacer(1,9),FloorPlan(),Spacer(1,12),box('Have these ready','Your floor sketches, a tape or laser measure, and a phone or tablet with a camera and internet access. Enter measurement fields in <b>metres</b>. Label any other units clearly in notes.'),Spacer(1,10),P(f'<b>Open the survey app:</b> <link href="{APP}" color="#2563eb">urbanfold.github.io/property-survey</link>','small'))
add(PageBreak())

# Page two: accounts, basic details, outside photos and proposal.
add(P('START YOUR SURVEY','tag'),P('Your property &amp; proposal','h1'))
heading('01','Sign up, log in or resume')
add(P('First visit? Choose <b>Sign Up</b>, enter your details and create a password. Confirm your email if prompted. Returning clients: choose <b>Log In</b> and use your <b>email address and password</b>.'))
add(P('In <b>My Surveys</b>, choose <b>+ Start New Survey</b>, or select a saved property to continue. Previously saved information remains available when you reopen that survey.'))
heading('02','Property Details')
add(P('Enter your name, client email address, property address and postcode. In <b>Property Details / Notes</b>, give a short overview of the extension, loft conversion or other work you are planning. Choose <b>Save &amp; Continue</b>.'))
heading('03','Property Type')
add(P('Choose the option that best describes your home, then select <b>Continue to Exterior Photos</b>.'))
heading('04','Exterior Elevations')
add(P('Take clear photos of every elevation requested by the app. Include the whole wall where possible, with windows, doors and roof details visible. Add extra views of attached structures, such as a conservatory, under the relevant elevation.'))
add(P('You can add multiple photos for each elevation. Use wide views for context and closer views for important details. Select the blue <b>Finish Existing Exterior</b> button when complete.'))
heading('05','Extension Details')
add(P('Select the proposal’s position and type. Describe how you want to use the space and the features you have in mind—for example, French doors, a flat or pitched roof, rooflights or an open-plan kitchen. Include as much useful detail as you can.'))
add(P('Enter the approximate proposed <b>width and length in metres</b>. Take photos of the proposed location, including possible obstructions such as drains, trees, changes in ground level or existing structures. Select <b>Continue to Interior</b>.'))
add(Spacer(1,5),box('Share your inspiration','Include inspiration images if your device lets you select existing photos. If the camera opens without a gallery option, email them to <b>survey@urbanfold.uk</b> and include the property address.'))
add(PageBreak())

# Page three: interior work and actual entry units.
add(P('RECORD THE INSIDE','tag'),P('Floor plans &amp; room details','h1'))
heading('06','Interior Floor Plans')
add(P('Photograph the floor-plan sketches you prepared earlier. Include a separate, clearly labelled sketch for every floor level. Check that room names, windows, doors and the proposed work are readable. Select <b>Continue to Room Details</b>.'))
heading('07','Measure and photograph each room')
add(box('Use the same measurement directions in every room',
    '<b>Width:</b> measure parallel to the front of the house.<br/>'
    '<b>Length:</b> measure at 90° to the front of the house, in the front-to-back direction.<br/>'
    'Keep these directions consistent in every room and label them on your floor sketches.'),Spacer(1,8))
for text in [
 'Open each relevant room and choose its shape. Include hallways and landings. If a room is not listed, use <b>Other</b> and identify it in Additional Measurements.',
 'Enter <b>length, width and height in metres</b>. Measure height from the finished floor to the ceiling. For an L-shaped room, complete the requested dimension fields and label the matching measurements on your sketch.',
 'Use <b>Additional Measurements</b> for chimney breasts, alcoves, recesses or other features. Name each feature, state its dimensions and label the units.',
 'Take a wide photo from a corner so it shows as much of the room as possible. Add more views to show details that are hidden in the first photo.',
 'After each room, scroll down and choose <b>Save progress</b>. Wait for the cloud-save confirmation before moving on or leaving the app.'
]:add(bullet(text))
add(Spacer(1,5),box('Example measurements','A room measuring 3,272 mm long is entered as <b>3.272 m</b>.<br/>Additional Measurements: “Chimney breast: <b>1,200 mm wide × 300 mm projection</b>, centred on the rear wall.”'),Spacer(1,6))
add(P('Optional: Leica Bluetooth entry','h2'),P('Manual entry works with a tape or laser measure. Automatic transfer has been tested with a <b>Leica DISTO S910 and Chrome on a Galaxy tablet</b>; other devices may differ. Keep the DISTO set to metres.','small'))
for text in [
 'Choose <b>Connect Leica</b>, then <b>Choose Leica device</b> and select your DISTO.',
 'Take a reading, check the received value against the laser, then select <b>Reading matches — enable room entry</b>.',
 'Tap the required Length, Width or Height field; it highlights blue. Take a <b>new</b> measurement. Select the next field before taking another reading.'
]:add(P('• '+text,'small'))
add(P('Tapping Close before enabling room entry disconnects the laser. Leaving Room Details also disconnects it. Continue to use <b>Save progress</b> for cloud storage.','small'))
add(PageBreak())

# Page four: review and the precise agreed business sequence.
add(P('FINISH WITH CONFIDENCE','tag'),P('Review, submit &amp; next steps','h1'))
heading('08','Check your survey and submit')
add(P('Choose <b>Review survey</b>. Check the property details, proposal, completed rooms and photo counts. The review helps you spot missing information; use the edit buttons to return to a section and check individual measurements.'))
for text in [
 'Property address, postcode and client email are correct.',
 'All requested exterior views and proposal-location photos are included.',
 'Every floor sketch is uploaded and clearly labelled.',
 'Relevant rooms have measurements, extra feature notes and photos.'
]:add(bullet(text))
add(P('When you are happy, select <b>Confirm &amp; submit survey</b>. Wait for the <b>Submission Successful</b> screen. Check the notification status shown separately; if email could not be confirmed, your survey may still be saved—do not submit again just to retry the email.'))
add(P('What happens next?','h2'))
steps=[
 ('We review your information','Our team checks your survey and may contact you if anything needs clarifying.'),
 ('You receive a draft 3D view','We prepare a draft 3D view showing your property with the proposal in position. You review it and tell us about any changes you would like.'),
 ('You approve the concept','Once you approve the proposal, we request a <b>50% deposit</b> and send a contract with terms and conditions for you to sign and return.'),
 ('We prepare your plans','Once the deposit is received and the signed contract is returned, we begin producing the agreed drawing package.')
]
for i,(title,body) in enumerate(steps,1):
    row=Table([[P(f'<b>{i:02}</b>','box'),P('<b>'+title+'</b><br/>'+body,'box')]],colWidths=[31,CW-31])
    row.setStyle(TableStyle([('VALIGN',(0,0),(-1,-1),'TOP'),('TEXTCOLOR',(0,0),(0,0),BLUE),('LEFTPADDING',(0,0),(-1,-1),0),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7)]))
    add(row)
add(Spacer(1,8),box('Pause and return whenever you need','Use <b>Save progress</b> and wait for confirmation that progress is verified in the cloud. To continue later, log in and choose the property from <b>My Surveys</b>. After submission, contact Urbanfold if the property address needs correcting.'),Spacer(1,8),P('Need help? Email <link href="mailto:survey@urbanfold.uk" color="#2563eb"><b>survey@urbanfold.uk</b></link> and include the property address.','small'))

doc=SimpleDocTemplate(str(OUT),pagesize=A4,rightMargin=44,leftMargin=44,topMargin=70,bottomMargin=59,title='Urbanfold | Client Self-Survey Guide',author='Urbanfold',subject='Step-by-step instructions for the Urbanfold property survey app',pageCompression=1)
doc.build(story,onFirstPage=page,onLaterPages=page)
print(OUT)
