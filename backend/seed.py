"""Run once: python seed.py  -> builds rollcall.db with demo accounts, sections, students, history."""
import random
from itertools import product
from pathlib import Path
from werkzeug.security import generate_password_hash
import db

DB = Path(__file__).with_name('rollcall.db')
PASSWORDS = {'administrator': 'Admin@123', 'instructor': 'Instructor@123', 'student': 'Student@123'}
SECTIONS = [('BSIT 2A', 'Database Management', 'Room 204', 'Mon / Thu · 9:00–10:30 AM'),
            ('BSIT 2B', 'Web Development', 'Computer Lab', 'Tue / Thu · 11:00 AM–12:30 PM'),
            ('BSIT 2C', 'Database Management', 'Room 204', 'Mon / Thu · 1:00–2:30 PM'),
            ('BSIT 3A', 'Information Systems', 'Room 301', 'Tue / Thu · 3:00–4:30 PM')]
FIXED = [('Alex', 'Reyes', '2024-0018'), ('Bea', 'Cruz', '2024-0021'), ('Carlo', 'Mendoza', '2024-0024'),
         ('Dani', 'Ramos', '2024-0028'), ('Elise', 'Torres', '2024-0030'), ('Felix', 'Garcia', '2024-0034'),
         ('Gia', 'Navarro', '2024-0039'), ('Hugo', 'Lim', '2024-0042')]  # match the UI mockups (BSIT 2A)
FIRST = 'Ana Ben Chloe Dino Ella Finn Gabe Hana Ivan Jade Kyle Lara Migs Nina Omar Pia Quin Rico Sofia Tito Uma Vince Wren Xavi Yna Zed'.split()
LAST = 'Aquino Bautista Castro Diaz Enriquez Flores Gomez Hernandez Ignacio Javier Katigbak Lopez Manalo Natividad Ocampo Pascual Quizon Rivera Salazar Tan'.split()
DATES = ['2026-10-01', '2026-10-05', '2026-10-08', '2026-10-12', '2026-10-15', '2026-10-19', '2026-10-21', '2026-10-22']


def main():
    rnd = random.Random(42)
    DB.unlink(missing_ok=True)
    con = db.init_schema(DB)
    h = {r: generate_password_hash(p) for r, p in PASSWORDS.items()}  # one salt per role: fast demo seeding

    def user(email, role, name):
        return con.execute('INSERT INTO users(email,password_hash,name,role) VALUES(?,?,?,?)',
                           (email, h[role], name, role)).lastrowid

    user('admin@school.edu', 'administrator', 'Andrea Cruz')
    teacher = user('instructor@school.edu', 'instructor', 'Maria Santos')

    names = [(f, l) for f, l in product(FIRST, LAST) if (f, l) not in {(a, b) for a, b, _ in FIXED}]
    rnd.shuffle(names)
    used, n = {i for *_, i in FIXED}, 0
    student_ids = {}
    for sid, (code, subj, room, sched) in enumerate(SECTIONS, 1):
        con.execute('INSERT INTO sections(id,code,subject,room,schedule,instructor_id) VALUES(?,?,?,?,?,?)',
                    (sid, code, subj, room, sched, teacher))
        people = list(FIXED) if sid == 1 else []
        while len(people) < 32:
            n += 1
            while (num := f'2024-{n:04d}') in used:
                n += 1
            used.add(num)
            f, l = names.pop()
            people.append((f, l, num))
        student_ids[sid] = []
        for f, l, num in people:
            uid = user(f'{f}.{l}@student.rollcall.local'.lower(), 'student', f'{f} {l}')
            student_ids[sid].append(con.execute(
                'INSERT INTO students(student_number,name,section_id,user_id) VALUES(?,?,?,?)',
                (num, f'{f} {l}', sid, uid)).lastrowid)

    for sid, ids in student_ids.items():
        for d in DATES:
            ses = con.execute('INSERT INTO class_sessions(section_id,session_date,created_by) VALUES(?,?,?)',
                              (sid, d, teacher)).lastrowid
            con.executemany('INSERT INTO attendance(session_id,student_id,status) VALUES(?,?,?)',
                            [(ses, s, rnd.choices(['present', 'late', 'absent', 'excused'], [86, 5, 7, 2])[0]) for s in ids])
    con.commit()
    print('Seeded:', *(f'{t}={con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]}'
                       for t in ('users', 'sections', 'students', 'class_sessions', 'attendance')))


if __name__ == '__main__':
    main()