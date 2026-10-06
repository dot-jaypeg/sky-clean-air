"""The /our-team/ page, generated from src/data/team.json.

Grouped by department (Management, HVAC Installation Team, Technicians &
Helpers), each person with their photo, role, a short bio and their
duties. Departments with no members yet, and people whose role we still
need from the client (`role_pending`), show a "coming soon" note while
site.json → show_placeholders is on.
"""
from sitelib import breadcrumb_schema, cta_band, esc, icon, page_hero, placeholder


def member_card(ch, m):
    if m.get('name_pending'):
        # Photo from the team shoot, name not confirmed yet — never guess a name.
        m = dict(m, name='Sky Clean Air Crew', role=m.get('role') or 'Team Member')
        if ch.s.get('show_placeholders'):
            m['role_pending'] = True
    photo = (f'<img src="{m["photo"]}" alt="{esc(m["name"])}, {esc(m["role"])} at Sky Clean Air" loading="lazy">'
             if m.get('photo') else f'<div class="team-photo-ph">{icon("user", 48)}</div>')
    duties = ''.join(f'<li>{esc(d)}</li>' for d in m.get('duties', []))
    facts = ''.join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in m.get('facts', []))
    pending = ''
    if m.get('role_pending') and ch.s.get('show_placeholders'):
        pending = '<p class="team-pending">Name, role &amp; duties coming soon</p>' if m.get('name_pending') else '<p class="team-pending">Role &amp; duties coming soon</p>'
    nick = f' <span class="team-nick">“{esc(m["short"])}”</span>' if m.get('short') else ''
    return f'''<article class="team-card" data-reveal>
  <div class="team-photo">{photo}</div>
  <div class="team-body">
    <h3>{esc(m["name"])}{nick}</h3>
    <p class="team-role">{esc(m["role"])}</p>
    {f'<p class="team-bio">{esc(m["bio"])}</p>' if m.get('bio') else ''}
    {f'<h4>What {esc(m["name"].split()[0])} handles</h4><ul class="team-duties">{duties}</ul>' if duties else ''}
    {f'<dl class="team-facts">{facts}</dl>' if facts else ''}
    {pending}
  </div>
</article>'''


def team_page(site):
    D, ch = site.D, site.ch
    T = D.team
    crumbs = [('Home', '/'), ('About', '/about-us/'), ('Our Team', None)]
    nav = ''.join(f'<a href="#{d["slug"]}">{esc(d["name"])}</a>' for d in T['departments'])
    sections = []
    for i, dept in enumerate(T['departments']):
        cards = ''.join(member_card(ch, m) for m in dept['members'])
        if not dept['members']:
            cards = placeholder(ch, f'{dept["name"]} — photos & bios coming soon',
                                'New headshots from the team event will go here, with each installer’s role and duties.',
                                'ph-wide team-ph')
        bg = ' bg-soft' if i % 2 else ''
        sections.append(f'''<section class="section team-dept{bg}" id="{dept["slug"]}">
  <div class="container">
    <div class="section-head" data-reveal>
      <span class="kicker-num" aria-hidden="true">{i + 1:02d}</span>
      <h2>{esc(dept["name"])}</h2>
      <p>{esc(dept["blurb"])}</p>
    </div>
    <div class="team-grid{' team-grid-lead' if dept['slug'] == 'management' else ''}">{cards}</div>
  </div>
</section>''')
    people = [m for d in T['departments'] for m in d['members']]
    schema = {
        '@context': 'https://schema.org', '@type': 'Organization', 'name': D.site['name'], 'url': D.site['domain'] + '/',
        'founder': [{'@type': 'Person', 'name': 'Nadav Offer'}, {'@type': 'Person', 'name': 'Daniel Lezmy'}],
        'employee': [{'@type': 'Person', 'name': m['name'], 'jobTitle': m['role']} for m in people if not m.get('role_pending')],
    }
    site.add({
        'path': '/our-team/',
        'title': 'Meet Our Team | Sky Clean Air San Diego & Orange County',
        'description': 'Meet the Sky Clean Air team — founders Nadav Offer and Daniel Lezmy, our office and management team, HVAC installers and the technicians in our trucks every day.',
        'schema': [schema, breadcrumb_schema(D.site['domain'], crumbs)],
        'body': page_hero(ch, 'Meet The <span class="hl">Sky Clean Air</span> Team',
                          'A family-owned company runs on its people. Here’s who you’ll talk to on the phone, who plans your install, and who shows up at your door.',
                          crumbs, media=T.get('group_photo'), ctas=False,
                          extra=f'<nav class="dept-nav" aria-label="Departments">{nav}</nav>') +
                ''.join(sections) +
                f'''<section class="section-tight"><div class="container"><div class="join-band" data-reveal>
  <div><h2>Want To Join <span class="grad-text">The Team?</span></h2><p>We’re growing across Southern California and hiring people who care about doing the job right.</p></div>
  <a href="/careers/" class="btn btn-primary">See Open Roles &rarr;</a>
</div></div></section>''' + cta_band(ch),
    })
