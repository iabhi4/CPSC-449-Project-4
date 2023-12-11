import json
from fastapi import Depends, FastAPI, HTTPException
import redis

from enroll.api import check_class_exists, check_user


app = FastAPI()

def get_redis():
    return redis.Redis(host="127.0.0.1", port=6379)

@app.post("/subscribe/{studentid}/{classid}/{username}/{email}/{proxyURL}")
def subscribe_to_notification(
    studentid: int,
    classid: int,
    username: str,
    email: str,
    proxyURL: str = None,
    r=Depends(get_redis)
):
    """API for students to subscribe to enrollment notifications.
    
    Args:
        studentid: The student's ID.
        classid: The class ID.

    Returns:
        A json with a message indicating the student's subscription status.
    """
    check_user(studentid, username, email)
    class_item = check_class_exists(classid)
    if class_item.get('State') != 'active':
        raise HTTPException(
            status_code=409,
            detail=f"Class with ClassID {classid} is not active"
        )
    
    subscriptionKey = f"subscription:{studentid}"
    existingSubscriptions = r.get(subscriptionKey)
    if not existingSubscriptions:
        existingSubscriptions = {}
    else:
        existingSubscriptions = json.loads(existingSubscriptions)
    existingSubscriptions[classid] = {"email": email, "proxy": proxyURL}
    r.set(subscriptionKey, json.dumps(existingSubscriptions))

    return {"message": f"You have subscribed to {classid}'s notification"}


@app.get("/subscribe/list/{studentid}")
def list_subscriptions(studentid: int, r=Depends(get_redis)):
    """API to list all enrollment notification subscriptions for a student.
    
    Args:
        studentid: The student's ID.

    Returns:
        A list of class-id's student is subscribed to
    """
    classIdList = []
    subscriptionKey = f"subscription:{studentid}"
    existingSubscriptions = r.get(subscriptionKey)
    if not existingSubscriptions:
        return {"subscriptions": []}
    
    existingSubscriptions = json.loads(existingSubscriptions)
    for classId in existingSubscriptions:
        classIdList.append(classId)
    return {"subscriptions": classIdList}
    

@app.delete("/subscribe/remove/{studentid}/{classid}")
async def unsubscribe_from_notification(
    studentid: int,
    classid: int,
    r=Depends(get_redis)
):
    """API for students to unsubscribe from getting notifications for a specific class.
    
    Args:
        studentid: The student's ID.
        classid: The class ID.

    Returns:
        A json with a message indicating the unsubscription status.
    """
    subscriptionKey = f"subscription:{studentid}"
    existingSubscriptions = r.get(subscriptionKey)
    if not existingSubscriptions:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {studentid} is not subscribed to ClassID {classid}"
        )
    
    existingSubscriptions = json.loads(existingSubscriptions)
    if classid not in existingSubscriptions:
        raise HTTPException(
            status_code=404,
            detail=f"Student with ID {studentid} is not subscribed to ClassID {classid}"
        )
    print("existing" + existingSubscriptions)
    del existingSubscriptions[classid]
    r.set(subscriptionKey, json.dumps(existingSubscriptions))

    return {"message": f"Unsubscribed from ClassID {classid}"}
