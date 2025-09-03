from typing import List
from fastapi import FastAPI, Request, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from starlette import status
import dependencies
import security
import models
from database import engine, SessionLocal, Base
from starlette.middleware.sessions import SessionMiddleware
from datetime import datetime
from sqlalchemy import func
import json
from urllib.parse import urlencode
from typing import Optional

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")
templates.env.globals['urlencode'] = urlencode
app.add_middleware(SessionMiddleware, secret_key="092fb55ff2458652ec5872cf3e2762a76aa9f9f889bcad4b1a28994e307f79a6")
Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)
##########################################################USERS/ADMIN##################################################################
@app.get("/admin/user/add", response_class=HTMLResponse)
async def add_user_form(request: Request, admin : models.User = Depends(dependencies.get_current_admin)):
    # if curent_user.role == "admin":
    return templates.TemplateResponse("admin_user_add.html", {"request": request})
    # else:
    #     return RedirectResponse(url="/", status_code=303)

@app.post("/admin/user/add", response_class=RedirectResponse)
async def create_user(
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    name:str = Form(...),
    family:str = Form(...),
    role: str = Form(...),
    phone:str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
        admin:models.User = Depends(dependencies.get_current_admin)
):
    if admin.role != "admin":
        return RedirectResponse(url="/", status_code=303)

    db_user = db.query(models.User).filter(models.User.username == username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="نام کاربری تکراری است")


    new_user = models.User(
        username=username,
        email=email,
        hashed_password=password,
        role=role,
        status=status,
        name=name,
        family=family,
        phone=phone
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return RedirectResponse(url="/admin/users", status_code=303)
@app.post("/admin/user/update/{user_id}")
async def update_user(
    user_id: int,
    first_name: str = Form(...),
    last_name: str = Form(...),
    username: str = Form(...),
    email: str = Form(...),
    phone: str = Form(...),
    role: str = Form(...),
    status: str = Form(...),
    db: Session = Depends(get_db),
        admin:models.User = Depends(dependencies.get_current_admin)
):
    if admin.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")

    user.first_name = first_name
    user.last_name = last_name
    user.username = username
    user.email = email
    user.phone = phone
    user.role = role
    user.status = status
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)

@app.get("/admin/user/view/{user_id}", response_class=HTMLResponse)
async def view_user(user_id: int, request: Request, db: Session = Depends(get_db),
                    admin:models.User = Depends(dependencies.get_current_admin)):
    if admin.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    print(user.phone, user.email, user.role, user.status, user.name, user.family)
    return templates.TemplateResponse("admin_user_view.html", {"request": request, "user": user})

@app.get("/admin/user/edit/{user_id}", response_class=HTMLResponse)
async def edit_user(user_id: int, request: Request, db: Session = Depends(get_db), admin:models.User = Depends(dependencies.get_current_admin)):
    if admin.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    return templates.TemplateResponse("admin_user_edit.html", {"request": request, "user": user})

@app.get("/admin/user/delete/{user_id}", response_class=RedirectResponse)
async def delete_user(user_id: int, db: Session = Depends(get_db), admin:models.User = Depends(dependencies.get_current_admin)):
    if admin.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="کاربر یافت نشد")
    db.delete(user)
    db.commit()
    return RedirectResponse(url="/admin/users", status_code=303)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

###################################################################################################################################
@app.get("/admin/login", response_class=HTMLResponse)
async def admin_login_form(request: Request):
    return templates.TemplateResponse("login_admin.html", {"request": request})

@app.post("/admin/login", response_class=HTMLResponse)
async def admin_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    passw = ""
    if user :
     passw = user.hashed_password
    if not user or not (password == passw):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "نام کاربری یا رمز عبور اشتباه است"
        })

    if user.status != "active":
        return templates.TemplateResponse("property_map_list.html", {
            "request": request,
            "error": "حساب شما غیرفعال است"
        })

    # ذخیره کاربر در session
    request.session["user_id"] = user.id

    # هدایت بر اساس نقش
    if user.role == "admin":
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    else:
        return RedirectResponse(url="/advisor/dashboard", status_code=303)


@app.get("/advisor/login", response_class=HTMLResponse)
async def advisor_login_form(request: Request):
    return templates.TemplateResponse("login_advisor.html", {"request": request})


@app.post("/advisor/login", response_class=HTMLResponse)
async def advisor_login_submit(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    db: Session = Depends(get_db)
):
    user = db.query(models.User).filter(models.User.username == username).first()
    passw = ""
    if user:
        passw = user.hashed_password
    if not user or not (password == passw):
        return templates.TemplateResponse("index.html", {
            "request": request,
            "error": "نام کاربری یا رمز عبور اشتباه است"
        })

    if user.status != "active":
        return templates.TemplateResponse("property_map_list.html", {
            "request": request,
            "error": "حساب شما غیرفعال است"
        })

    # ذخیره کاربر در session
    request.session["user_id"] = user.id

    # هدایت بر اساس نقش
    if user.role == "admin":
        return RedirectResponse(url="/admin/dashboard", status_code=303)
    else:
        return RedirectResponse(url="/advisor/dashboard", status_code=303)

@app.get("/admin/dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, admin: models.User = Depends(dependencies.get_current_admin)):
    if admin.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("dashboard_admin.html", {"request": request})


@app.get("/advisor/dashboard", response_class=HTMLResponse)
async def advisor_dashboard(request: Request):
    return templates.TemplateResponse("dashboard_advisor.html", {"request": request})

@app.get("/admin/manage_properties", response_class=HTMLResponse)
async def admin_manage(request: Request, admin: models.User = Depends(dependencies.get_current_admin)):
    if admin.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("admin_manage_info.html", {"request": request})

@app.get("/admin/users", response_class=HTMLResponse)
async def admin_users(
    request: Request,
    search: str = None,
    role: str = None,
    page: int = 1,
    db: Session = Depends(get_db)
):
    ITEMS_PER_PAGE = 10
    offset = (page - 1) * ITEMS_PER_PAGE

    query = db.query(models.User)

    if search and search !='':
        query = query.filter(
            (models.User.username.contains(search)) | (models.User.email.contains(search))
        )
    if role and role != "":
        query = query.filter(models.User.role == role)

    total_count = query.count()
    total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    users = query.offset(offset).limit(ITEMS_PER_PAGE).all()

    # ساخت query_string برای صفحه‌بندی
    params = dict(request.query_params)
    params.pop('page', None)
    query_string = urlencode(params)

    return templates.TemplateResponse("admin_users.html", {
        "request": request,
        "users": users,
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "query_string": query_string
    })

####################################################property################################################################
@app.get("/admin/property/{property_id}/owner", response_class=HTMLResponse)
async def owner_info_form(property_id: int, request: Request, user: models.User = Depends(dependencies.get_current_user)):
    if not user :
        return RedirectResponse(url="/", status_code=303)
    return templates.TemplateResponse("owner_info_form.html", {"request": request, "property_id": property_id})

@app.get("/admin/properties", response_class=HTMLResponse)
async def property_map(request: Request, db: Session = Depends(get_db), admin:models.User = Depends(dependencies.get_current_admin)):
    if admin.role != "admin":
        return RedirectResponse(url="/", status_code=303)
    properties = db.query(models.Property).all()
    return templates.TemplateResponse("property_map_list.html", {"request": request, "properties": properties})

@app.get("/admin/property/add", response_class=HTMLResponse)
async def create_property(request: Request, user: models.User = Depends(dependencies.get_current_user), db: Session = Depends(get_db)):
    if not user :
        return RedirectResponse(url="/", status_code=303)
    if user.role == "admin":
        advisors = []
        advisors = db.query(models.User).filter(models.User.role == "advisor").all()
        return (templates.TemplateResponse
                    ("admin_property_add.html",
                     {"request":
                          request,
                          "advisors": advisors,
                          "current_user": user                        }
                    )
                )
    return templates.TemplateResponse("admin_property_add.html", {"request": request})


@app.post("/admin/property/add", response_class=RedirectResponse, )
async def create_property(
    title: str = Form(...),
    latitude: float = Form(...),
    longitude: float = Form(...),
    property_type: str = Form(...),
    facade_status: str = Form(None),
    price_total: int = Form(...),
    price_per_meter: int = Form(...),
    floor: int = Form(None),
    year_built: int = Form(None),
    units_in_building: int = Form(None),
    bedrooms: int = Form(None),
    length: int = Form(None),
    width: int = Form(None),
    size: int = Form(None),
    neighborhood: str = Form(None),
    detailed_address: str = Form(None),
    amenities: List[str] = Form([]),
    description: str = Form(None),
    advisor_id: int = Form(0),  # پیش‌فرض 0 یعنی خود ادمین
    db: Session = Depends(get_db),
    current_user: models.User = Depends(dependencies.get_current_user)
):
    # تبدیل امکانات به رشته
    amenities_str = ",".join(amenities) if amenities else None

    # ایجاد ملک جدید
    if advisor_id == 0:
        advisor_id = current_user.id

    new_property = models.Property(
        title=title,
        locationOnMap= str(latitude)+","+str(longitude),
        latitude=latitude,
        longitude=longitude,
        property_type=property_type,
        facade_status=facade_status,
        price=price_total,
        pricePerMeter=price_per_meter,
        floorNumber=floor,
        builtYear=year_built,
        units_in_building=units_in_building,
        bedrooms=bedrooms,
        length=length,
        width=width,
        size= size,
        neighborhood=neighborhood,
        detailed_address=detailed_address,
        amenities=amenities_str,
        description=description,
        adviosor_id= advisor_id
    )
    print(new_property)
    db.add(new_property)
    db.commit()
    db.refresh(new_property)

    #
    #
    # هدایت به لیست ملک‌ها
    query = db.query(models.Property)
    query = query.filter(models.Property.latitude == latitude)
    query = query.filter(models.Property.longitude == longitude)
    result = query.first()
    property_id = -1
    if result :
        property_id = result.id
    return RedirectResponse(url=f"/admin/property/{property_id}/owner", status_code=303)


@app.get("/admin/reports", response_class=HTMLResponse)
async def admin_reports(
    request: Request,
    start_date: str = None,
    end_date: str = None,
    db: Session = Depends(get_db)
):
    query = db.query(models.Property)

    if start_date:
        try:
            query = query.filter(models.Property.RegisterDateNational >= start_date)
        except:
            pass

    if end_date:
        try:
            query = query.filter(models.Property.RegisterDateNational <= end_date)
        except:
            pass

    properties = query.all()

    # محاسبات
    deal_count = {}
    for p in properties:
        t = p.property_type or "نامشخص"
        deal_count[t] = deal_count.get(t, 0) + 1

    status_count = {}
    for p in properties:
        s = p.status
        status_count[s] = status_count.get(s, 0) + 1

    advisor_count = {}
    for p in properties:
        if p.adviosor_id and p.adviosor_id != 0:
            advisor = db.query(models.User).filter(models.User.id == p.adviosor_id).first()
            name = advisor.username if advisor else f"مشاور {p.adviosor_id}"
            advisor_count[name] = advisor_count.get(name, 0) + 1

    # ارسال داده با پیش‌فرض
    chart_data = {
        "deal_labels": list(deal_count.keys()) or ["نامشخص"],
        "deal_values": list(deal_count.values()) or [0],
        "status_labels": list(status_count.keys()) or ["غیرفعال"],
        "status_values": list(status_count.values()) or [0],
        "advisor_names": list(advisor_count.keys()) or ["ندارد"],
        "advisor_counts": list(advisor_count.values()) or [0]
    }

    return templates.TemplateResponse("admin_reports.html", {
        "request": request,
        "chart_data": chart_data
    })

@app.post("/admin/owner/add", response_class=RedirectResponse)
async def save_owner(
    property_id: int = Form(...),
    name: str = Form(...),
    Family: str = Form(...),
    phone: str = Form(...),
    db: Session = Depends(get_db),
    user: models.User = Depends(dependencies.get_current_user)
):
    # چک کردن وجود ملک
    property = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="ملک یافت نشد")

    # ایجاد مالک جدید
    new_owner = models.Owner(
        name=name,
        Family=Family,
        phone=phone,
        DISC_test=str(1234)  # میتونه None باشه
    )

    db.add(new_owner)
    db.commit()
    db.refresh(new_owner)

    query = db.query(models.Owner)
    query = query.filter(models.Owner.name == name)
    query = query.filter(models.Owner.Family == Family)
    query = query.filter(models.Owner.phone == phone)
    result = query.first().id
    if result :
        property.owner_id = result

    db.commit()
    db.refresh(new_owner)
    if user.role == "admin" :
     return RedirectResponse(url="/admin/properties", status_code=303)

    return RedirectResponse(url="/advisor/properties/my", status_code=303)


@app.get("/admin/property/view/{prop_id}", response_class=HTMLResponse)
async def view_property(prop_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(dependencies.get_current_user)):
    # گرفتن ملک
    property = db.query(models.Property).filter(models.Property.id == prop_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="ملک یافت نشد")

    # گرفتن مالک (اگر وجود داشت)
    owner = None
    if property.owner_id:
        owner = db.query(models.Owner).filter(models.Owner.id == property.owner_id).first()

    # گرفتن مشاور (اگر وجود داشت)
    advisor = None
    if property.adviosor_id and property.adviosor_id != 0:
        advisor = db.query(models.User).filter(models.User.id == property.adviosor_id).first()

    return templates.TemplateResponse("admin_property_view.html", {
        "request": request,
        "property": property,
        "owner": owner,
        "advisor": advisor
    })
@app.get("/admin/search", response_class=HTMLResponse)
async def admin_search(
    request: Request,
    neighborhood = None,
    owner_phone = None,
    min_price = None,
    max_price = None,
    min_area = None,
    max_area = None,
    room_number = None,
    property_type= None,
    page: int = 1,
    db: Session = Depends(get_db)
):
    ITEMS_PER_PAGE = 10
    offset = (page - 1) * ITEMS_PER_PAGE

    query = db.query(models.Property)

    if neighborhood and neighborhood != "":
        query = query.filter(models.Property.neighborhood.contains(neighborhood))
    if min_price and min_price != "":
        min_price = int(min_price)
        query = query.filter(models.Property.price >= min_price)
    if max_price and max_price != "":
        max_price = int(max_price)
        query = query.filter(models.Property.price <= max_price)
    if min_area and min_area != "":
        min_area = int(min_area)
        query = query.filter(models.Property.size >= min_area)
    if max_area and max_area != "":
        max_area = int(max_area)
        query = query.filter(models.Property.size <= max_area)
    if room_number and room_number != "":
        room_number = int(room_number)
        query = query.filter(models.Property.bedrooms == room_number)
    # if property_type:
    #     query = query.filter(models.Property.property_type == property_type)

    total_count = query.count()
    total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    results = query.offset(offset).limit(ITEMS_PER_PAGE).all()

    # حذف 'page' از پارامترها و ساخت کوئری استرینگ
    params = dict(request.query_params)
    params.pop('page', None)
    query_string = urlencode(params)

    return templates.TemplateResponse("admin_property_search.html", {
        "request": request,
        "results": results,
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "query_string": query_string
    })

@app.get("/admin/property/view/{prop_id}")
async def view_property(prop_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(dependencies.get_current_user)):
    prop = db.query(models.Property).filter(models.Property.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="ملک یافت نشد")
    return templates.TemplateResponse("admin_property_view.html", {"request": request, "prop": prop})


@app.get("/admin/property/edit/{prop_id}", response_class=HTMLResponse)
async def edit_property(prop_id: int, request: Request, db: Session = Depends(get_db), user: models.User = Depends(dependencies.get_current_user)):
    prop = db.query(models.Property).filter(models.Property.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="ملک یافت نشد")
    return templates.TemplateResponse("admin_property_edit.html", {"request": request, "property": prop})


@app.post("/admin/property/update/{prop_id}", response_class=RedirectResponse)
async def update_property(
    prop_id: int,
    title: str = Form(...),
    latitude: str = Form(...),
    longitude: str = Form(...),
    property_type: str = Form(...),
    facade_status: str = Form(...),
    price: int = Form(...),
    pricePerMeter: int = Form(...),
    floorNumber: int = Form(...),
    builtYear: int = Form(...),
    units_in_building: int = Form(None),
    bedrooms: int = Form(None),
    area: int = Form(None),
    length: int = Form(...),
    width: int = Form(...),
    neighborhood: str = Form(...),
    status: str = Form(...),
    detailed_address: str = Form(...),
    amenities: list = Form([]),
    description: str = Form(None),
    db: Session = Depends(get_db),
    user: models.User = Depends(dependencies.get_current_user)
):
    property = db.query(models.Property).filter(models.Property.id == prop_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="ملک یافت نشد")

    # بروزرسانی فیلدها
    property.title = title
    property.latitude = latitude
    property.longitude = longitude
    property.property_type = property_type
    property.facade_status = facade_status
    property.price = price
    property.pricePerMeter = pricePerMeter
    property.floorNumber = floorNumber
    property.builtYear = builtYear
    property.units_in_building = units_in_building
    property.bedrooms = bedrooms
    property.length = length
    property.width = width
    property.neighborhood = neighborhood
    property.detailed_address = detailed_address
    property.amenities = ",".join(amenities) if amenities else None
    property.description = description
    property.status = status
    property.size = area

    db.commit()
    if user.role == "admin":
        return RedirectResponse(url="/admin/properties", status_code=303)
    return RedirectResponse(url="/advisor/properties/my", status_code=303)
@app.get("/admin/property/delete/{prop_id}")
async def delete_property(prop_id: int, db: Session = Depends(get_db), user: models.User = Depends(dependencies.get_current_user)):
    prop = db.query(models.Property).filter(models.Property.id == prop_id).first()
    if not prop:
        raise HTTPException(status_code=404, detail="ملک یافت نشد")
    db.delete(prop)
    db.commit()
    return RedirectResponse(url="/admin/properties", status_code=303)
########################################################################################################################################
@app.get("/advisor/dashboard", response_class=HTMLResponse)
async def advisor_dashboard(request: Request, user: models.User = Depends(dependencies.get_current_user)):
    return templates.TemplateResponse("advisor_dashboard.html", {"request": request})

# فرم افزودن ملک
@app.get("/advisor/property/add", response_class=HTMLResponse)
async def advisor_add_property_form(request: Request,user: models.User = Depends(dependencies.get_current_user)):
    return templates.TemplateResponse("advisor_property_add.html", {"request": request})


@app.get("/advisor/properties/my", response_class=HTMLResponse)
async def my_properties(request: Request, db: Session = Depends(get_db),
                        current_user: models.User = Depends(dependencies.get_current_user)):
    # فرض میکنیم کاربر لاگین کرده و نقشش "advisor" است
    # ملک‌هایی که با adviosor_id مشاور ثبت شدن
    properties = db.query(models.Property).filter(models.Property.adviosor_id == current_user.id).all()

    return templates.TemplateResponse("advisor_properties_list.html", {
        "request": request,
        "properties": properties
    })

# فرم جستجو
@app.get("/advisor/properties/my", response_class=HTMLResponse)
async def my_properties(
        request: Request,
        db: Session = Depends(get_db),
        current_user: models.User = Depends(dependencies.get_current_user)
):
    # فقط ملک‌هایی که با این مشاور ثبت شدن
    properties = db.query(models.Property).filter(models.Property.adviosor_id == current_user.id).all()

    return templates.TemplateResponse("advisor_properties_list.html", {
        "request": request,
        "properties": properties
    })


@app.get("/advisor/property/view/{property_id}", response_class=HTMLResponse)
async def view_property_for_advisor(
    property_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    # دریافت ملک
    property = db.query(models.Property).filter(models.Property.id == property_id).first()
    if not property:
        raise HTTPException(status_code=404, detail="ملک یافت نشد")

    # دریافت مشاور
    advisor = db.query(models.User).filter(models.User.id == property.adviosor_id).first()
    if not advisor:
        raise HTTPException(status_code=404, detail="مشاور یافت نشد")

    return templates.TemplateResponse("advisor_property_view.html", {
        "request": request,
        "property": property,
        "advisor": advisor
    })
@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}





@app.get("/advisor/property/search", response_class=HTMLResponse)
async def advisor_search(
    request: Request,
    neighborhood=None,
    min_price=None,
    max_price=None,
    min_area=None,
    max_area=None,
    room_number=None,
    property_type=None,
    page: int = 1,
    db: Session = Depends(get_db)
):
    ITEMS_PER_PAGE = 10
    offset = (page - 1) * ITEMS_PER_PAGE

    query = db.query(models.Property)

    if neighborhood and neighborhood != "":
        query = query.filter(models.Property.neighborhood.contains(neighborhood))
    if min_price and min_price != "":
        min_price = int(min_price)
        query = query.filter(models.Property.price >= min_price)
    if max_price and max_price != "":
        max_price = int(max_price)
        query = query.filter(models.Property.price <= max_price)
    if min_area and min_area != "":
        min_area = int(min_area)
        query = query.filter(models.Property.size >= min_area)
    if max_area and max_area != "":
        max_area = int(max_area)
        query = query.filter(models.Property.size <= max_area)
    if room_number and room_number != "":
        room_number = int(room_number)
        query = query.filter(models.Property.bedrooms == room_number)
    # if property_type:
    #     query = query.filter(models.Property.property_type == property_type)

    total_count = query.count()
    total_pages = (total_count + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    results = query.offset(offset).limit(ITEMS_PER_PAGE).all()

    # حذف 'page' از پارامترها و ساخت کوئری استرینگ
    params = dict(request.query_params)
    params.pop('page', None)
    query_string = urlencode(params)

    return templates.TemplateResponse("advisor_property_search.html", {
        "request": request,
        "results": results,
        "total_count": total_count,
        "total_pages": total_pages,
        "page": page,
        "query_string": query_string
    })
