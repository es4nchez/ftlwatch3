


from _dbConnector import *
from _api import *
import click


# any(isinstance(e, int) and e > 0 for e in [1,2,'joe'])
# all(isinstance(e, int) and e > 0 for e in [1,2,'joe'])

local_teams = []
current_limit = 50
limit_checker = 50

def user_points_callback(transac, user_id, login):
    global local_points, current_limit, limit_checker
    from _utils_mylogger import mylogger, LOGGER_DEBUG, LOGGER_INFO, LOGGER_WARNING, LOGGER_ERROR

    if (transac['id'] not in local_points):
        current_limit = limit_checker

        mylogger(f"Import point for {user_id} {login}, {transac['sum']} {transac['reason']} / current_limit = {current_limit}", LOGGER_INFO)

        good = {
            "id": transac['id'],
            "user_id": user_id,
            "reason": transac['reason'],
            "sum": transac['sum'],
            "total": transac['total'],
            "created_at": transac['created_at'],
            "updated_at": transac['updated_at'],
        }

        executeQueryAction("""INSERT INTO points_transactions (
                "id", "user_id", "reason", "sum", "total", "created_at", "updated_at"
            ) VALUES (
                %(id)s, %(user_id)s, %(reason)s, %(sum)s, %(total)s, %(created_at)s, %(updated_at)s
            )
            ON CONFLICT DO NOTHING
            """, good)
        
    else:
        current_limit -= 1

    return (current_limit > 0)


def import_points(update_all=False, start_at=1):
    global local_points
    from _utils_mylogger import mylogger, LOGGER_ALERT

    to_check = executeQuerySelect("""SELECT id, login FROM users WHERE kind = 'student' AND (blackhole > NOW() OR grade = 'Member') ORDER BY id""")

    mylogger("Start users points worker", LOGGER_ALERT)

    for check in to_check:

        local_points = executeQuerySelect("SELECT id FROM points_transactions WHERE user_id = %(user_id)s ORDER BY id DESC LIMIT 1000", {
            "user_id": check['id']
        })
        local_points = [one['id'] for one in local_points] 

        if (len(local_points) == 0):
            update_all = True

        if (update_all):
            callapi(f"/v2/users/{check['login']}/correction_point_historics?sort=id", nultiple=start_at, callback=lambda x: user_points_callback(x, check['id'], check['login']), callback_limit=False)

        else:
            callapi(f"/v2/users/{check['login']}/correction_point_historics?sort=-id", nultiple=1, callback=lambda x: user_points_callback(x, check['id'], check['login']), callback_limit=True)

        time.sleep(0.4)

    mylogger("End users points worker", LOGGER_ALERT)


@click.command()
@click.option("--update-all", "-a", type=bool, default=False, help="update all")
@click.option("--start-at", "-s", type=int, default=1, help="start at")

def starter(update_all=False, start_at=1):
    import_points(update_all, start_at)

if __name__ == "__main__":
    starter()