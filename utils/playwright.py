def clear_cookie_by_name(context, cookie_cleared_name):
    cookies = context.cookies()
    filtered_cookies = [cookie for cookie in cookies if cookie["name"] != cookie_cleared_name]
    context.clear_cookies()
    context.add_cookies(filtered_cookies)

def unhide_spoiler_content(page):
    spoiler_containers = page.locator("shreddit-blurred-container[reason='spoiler']")
    for i in range(spoiler_containers.count()):
        container = spoiler_containers.nth(i)
        if container.is_visible():
            container.locator("text=View spoiler").click()