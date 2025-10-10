uv run uvicorn apps.user.main:create_app --factory --reload --port 8011
INFO:     Will watch for changes in these directories: ['/Users/adam/dev/multicardz']
INFO:     Uvicorn running on http://127.0.0.1:8011 (Press CTRL+C to quit)
INFO:     Started reloader process [97384] using StatReload
INFO:apps.user.main:MultiCardz™ User Application initialized
INFO:     Started server process [97386]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:apps.shared.middleware.request_interceptor:REQUEST: GET /
INFO:apps.user.main:Tutorial database tags: [{'id': 'column_tag_1', 'name': 'column1', 'count': 1}, {'id': 'intersection_tag_1', 'name': 'intersection1', 'count': 1}, {'id': 'row_tag_1', 'name': 'row1', 'count': 1}, {'id': 'union_tag_1', 'name': 'union1', 'count': 2}, {'id': 'union_tag_2', 'name': 'union2', 'count': 3}]
DEBUG: Loading 5 tags from tutorial database: [{'id': 'column_tag_1', 'name': 'column1', 'count': 1}, {'id': 'intersection_tag_1', 'name': 'intersection1', 'count': 1}, {'id': 'row_tag_1', 'name': 'row1', 'count': 1}, {'id': 'union_tag_1', 'name': 'union1', 'count': 2}, {'id': 'union_tag_2', 'name': 'union2', 'count': 3}]
INFO:apps.user.main:Loading 5 tags
INFO:apps.shared.middleware.request_interceptor:RESPONSE: GET / - 200 (21.73ms)
INFO:     127.0.0.1:51854 - "GET /?lesson=2 HTTP/1.1" 200 OK
INFO:apps.shared.middleware.request_interceptor:REQUEST: GET /.well-known/appspecific/com.chrome.devtools.json
INFO:apps.shared.middleware.request_interceptor:REQUEST: GET /api/user/preferences
INFO:apps.shared.middleware.request_interceptor:RESPONSE: GET /.well-known/appspecific/com.chrome.devtools.json - 404 (7.30ms)
INFO:     127.0.0.1:51854 - "GET /.well-known/appspecific/com.chrome.devtools.json HTTP/1.1" 404 Not Found
INFO:     127.0.0.1:51855 - "GET /api/user/preferences HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
  + Exception Group Traceback (most recent call last):
  |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_utils.py", line 79, in collapse_excgroups
  |     yield
  |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 183, in __call__
  |     async with anyio.create_task_group() as task_group:
  |                ~~~~~~~~~~~~~~~~~~~~~~~^^
  |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 772, in __aexit__
  |     raise BaseExceptionGroup(
  |         "unhandled errors in a TaskGroup", self._exceptions
  |     ) from None
  | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/protocols/http/h11_impl.py", line 403, in run_asgi
    |     result = await app(  # type: ignore[func-returns-value]
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |         self.scope, self.receive, self.send
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |     )
    |     ^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    |     return await self.app(scope, receive, send)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/applications.py", line 1054, in __call__
    |     await super().__call__(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/applications.py", line 113, in __call__
    |     await self.middleware_stack(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 186, in __call__
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 164, in __call__
    |     await self.app(scope, receive, _send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 29, in __call__
    |     await responder(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 130, in __call__
    |     await super().__call__(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 46, in __call__
    |     await self.app(scope, receive, self.send_with_compression)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 182, in __call__
    |     with recv_stream, send_stream, collapse_excgroups():
    |                                    ~~~~~~~~~~~~~~~~~~^^
    |   File "/opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/lib/python3.13/contextlib.py", line 162, in __exit__
    |     self.gen.throw(value)
    |     ~~~~~~~~~~~~~~^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_utils.py", line 85, in collapse_excgroups
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 184, in __call__
    |     response = await self.dispatch_func(request, call_next)
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 60, in dispatch
    |     return await intercept_request(request, call_next)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 42, in intercept_request
    |     response = await call_next(request)
    |                ^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 159, in call_next
    |     raise app_exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 144, in coro
    |     await self.app(scope, receive_or_disconnect, send_no_error)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    |     await app(scope, receive, sender)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 716, in __call__
    |     await self.middleware_stack(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 736, in app
    |     await route.handle(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 290, in handle
    |     await self.app(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 78, in app
    |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    |     await app(scope, receive, sender)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 75, in app
    |     response = await f(request)
    |                ^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 302, in app
    |     raw_response = await run_endpoint_function(
    |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |     ...<3 lines>...
    |     )
    |     ^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 213, in run_endpoint_function
    |     return await dependant.call(**values)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/apps/user/routes/cards_api.py", line 1084, in get_user_preferences
    |     from apps.shared.config.database import get_db_path
    | ImportError: cannot import name 'get_db_path' from 'apps.shared.config.database' (/Users/adam/dev/multicardz/apps/shared/config/database.py)
    +------------------------------------

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/protocols/http/h11_impl.py", line 403, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.scope, self.receive, self.send
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/applications.py", line 1054, in __call__
    await super().__call__(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/applications.py", line 113, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 29, in __call__
    await responder(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 130, in __call__
    await super().__call__(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 46, in __call__
    await self.app(scope, receive, self.send_with_compression)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 182, in __call__
    with recv_stream, send_stream, collapse_excgroups():
                                   ~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_utils.py", line 85, in collapse_excgroups
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 184, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 60, in dispatch
    return await intercept_request(request, call_next)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 42, in intercept_request
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 159, in call_next
    raise app_exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 290, in handle
    await self.app(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 78, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 75, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 302, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 213, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/apps/user/routes/cards_api.py", line 1084, in get_user_preferences
    from apps.shared.config.database import get_db_path
ImportError: cannot import name 'get_db_path' from 'apps.shared.config.database' (/Users/adam/dev/multicardz/apps/shared/config/database.py)
INFO:apps.shared.middleware.request_interceptor:REQUEST: GET /api/lessons/options
INFO:apps.shared.middleware.request_interceptor:RESPONSE: GET /api/lessons/options - 200 (0.47ms)
INFO:     127.0.0.1:51858 - "GET /api/lessons/options?completed=%5B%5D HTTP/1.1" 200 OK
INFO:apps.shared.middleware.request_interceptor:REQUEST: POST /api/render/cards
INFO:apps.user.routes.cards_api:Processing 6 zones
INFO:apps.user.routes.cards_api:Using database: /var/data/tutorial_customer.db
INFO:apps.user.routes.cards_api:Loading cards for lesson 1
INFO:apps.user.routes.cards_api:DB READ: card_id=card_union1_only, name=Card with union1 only
INFO:apps.user.routes.cards_api:CARD OBJECT: id=card_union1_only, title=Card with union1 only, tags=frozenset({'union1'})
INFO:apps.user.routes.cards_api:DB READ: card_id=card_union1_intersection1, name=Card with union1 and intersection1
INFO:apps.user.routes.cards_api:CARD OBJECT: id=card_union1_intersection1, title=Card with union1 and intersection1, tags=frozenset({'intersection1', 'union1'})
INFO:apps.user.routes.cards_api:DB READ: card_id=card_union2_only, name=Card with union2 only
INFO:apps.user.routes.cards_api:CARD OBJECT: id=card_union2_only, title=Card with union2 only, tags=frozenset({'union2'})
INFO:apps.user.routes.cards_api:DB READ: card_id=card_union2_column1, name=Card with union2 and column1
INFO:apps.user.routes.cards_api:CARD OBJECT: id=card_union2_column1, title=Card with union2 and column1, tags=frozenset({'union2', 'column1'})
INFO:apps.user.routes.cards_api:DB READ: card_id=card_union2_row1, name=Card with union2 and row1
INFO:apps.user.routes.cards_api:CARD OBJECT: id=card_union2_row1, title=Card with union2 and row1, tags=frozenset({'union2', 'row1'})
INFO:apps.user.routes.cards_api:Loaded 5 cards
INFO:apps.user.routes.cards_api:No operations, showing 0 always_visible cards
INFO:apps.user.routes.cards_api:Rendering dimensional grid: 0 cards, rows=[], cols=[]
INFO:apps.user.routes.cards_api:Converted 0 cards to template format
INFO:apps.user.routes.cards_api:Tag order for color assignment (alphabetical): []
INFO:apps.user.routes.cards_api:Successfully rendered dimensional grid HTML (376 chars)
INFO:apps.user.routes.cards_api:Request completed in 78.36ms
INFO:apps.shared.middleware.request_interceptor:RESPONSE: POST /api/render/cards - 200 (79.28ms)
INFO:     127.0.0.1:51858 - "POST /api/render/cards HTTP/1.1" 200 OK
INFO:apps.shared.middleware.request_interceptor:REQUEST: GET /api/lessons/hint
INFO:apps.shared.middleware.request_interceptor:RESPONSE: GET /api/lessons/hint - 200 (0.69ms)
INFO:     127.0.0.1:51858 - "GET /api/lessons/hint HTTP/1.1" 200 OK
INFO:apps.shared.middleware.request_interceptor:REQUEST: POST /api/user/preferences
INFO:     127.0.0.1:51858 - "POST /api/user/preferences HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
  + Exception Group Traceback (most recent call last):
  |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_utils.py", line 79, in collapse_excgroups
  |     yield
  |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 183, in __call__
  |     async with anyio.create_task_group() as task_group:
  |                ~~~~~~~~~~~~~~~~~~~~~~~^^
  |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 772, in __aexit__
  |     raise BaseExceptionGroup(
  |         "unhandled errors in a TaskGroup", self._exceptions
  |     ) from None
  | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/protocols/http/h11_impl.py", line 403, in run_asgi
    |     result = await app(  # type: ignore[func-returns-value]
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |         self.scope, self.receive, self.send
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |     )
    |     ^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    |     return await self.app(scope, receive, send)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/applications.py", line 1054, in __call__
    |     await super().__call__(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/applications.py", line 113, in __call__
    |     await self.middleware_stack(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 186, in __call__
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 164, in __call__
    |     await self.app(scope, receive, _send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 29, in __call__
    |     await responder(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 130, in __call__
    |     await super().__call__(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 46, in __call__
    |     await self.app(scope, receive, self.send_with_compression)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 182, in __call__
    |     with recv_stream, send_stream, collapse_excgroups():
    |                                    ~~~~~~~~~~~~~~~~~~^^
    |   File "/opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/lib/python3.13/contextlib.py", line 162, in __exit__
    |     self.gen.throw(value)
    |     ~~~~~~~~~~~~~~^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_utils.py", line 85, in collapse_excgroups
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 184, in __call__
    |     response = await self.dispatch_func(request, call_next)
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 60, in dispatch
    |     return await intercept_request(request, call_next)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 42, in intercept_request
    |     response = await call_next(request)
    |                ^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 159, in call_next
    |     raise app_exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 144, in coro
    |     await self.app(scope, receive_or_disconnect, send_no_error)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    |     await app(scope, receive, sender)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 716, in __call__
    |     await self.middleware_stack(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 736, in app
    |     await route.handle(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 290, in handle
    |     await self.app(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 78, in app
    |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    |     await app(scope, receive, sender)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 75, in app
    |     response = await f(request)
    |                ^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 302, in app
    |     raw_response = await run_endpoint_function(
    |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |     ...<3 lines>...
    |     )
    |     ^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 213, in run_endpoint_function
    |     return await dependant.call(**values)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/apps/user/routes/cards_api.py", line 1132, in save_user_preferences
    |     from apps.shared.config.database import get_db_path
    | ImportError: cannot import name 'get_db_path' from 'apps.shared.config.database' (/Users/adam/dev/multicardz/apps/shared/config/database.py)
    +------------------------------------

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/protocols/http/h11_impl.py", line 403, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.scope, self.receive, self.send
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/applications.py", line 1054, in __call__
    await super().__call__(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/applications.py", line 113, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 29, in __call__
    await responder(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 130, in __call__
    await super().__call__(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 46, in __call__
    await self.app(scope, receive, self.send_with_compression)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 182, in __call__
    with recv_stream, send_stream, collapse_excgroups():
                                   ~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_utils.py", line 85, in collapse_excgroups
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 184, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 60, in dispatch
    return await intercept_request(request, call_next)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 42, in intercept_request
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 159, in call_next
    raise app_exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 290, in handle
    await self.app(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 78, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 75, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 302, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 213, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/apps/user/routes/cards_api.py", line 1132, in save_user_preferences
    from apps.shared.config.database import get_db_path
ImportError: cannot import name 'get_db_path' from 'apps.shared.config.database' (/Users/adam/dev/multicardz/apps/shared/config/database.py)
INFO:apps.shared.middleware.request_interceptor:REQUEST: GET /
INFO:apps.user.main:Tutorial database tags: [{'id': 'column_tag_1', 'name': 'column1', 'count': 1}, {'id': 'intersection_tag_1', 'name': 'intersection1', 'count': 1}, {'id': 'row_tag_1', 'name': 'row1', 'count': 1}, {'id': 'union_tag_1', 'name': 'union1', 'count': 2}, {'id': 'union_tag_2', 'name': 'union2', 'count': 3}]
DEBUG: Loading 5 tags from tutorial database: [{'id': 'column_tag_1', 'name': 'column1', 'count': 1}, {'id': 'intersection_tag_1', 'name': 'intersection1', 'count': 1}, {'id': 'row_tag_1', 'name': 'row1', 'count': 1}, {'id': 'union_tag_1', 'name': 'union1', 'count': 2}, {'id': 'union_tag_2', 'name': 'union2', 'count': 3}]
INFO:apps.user.main:Loading 5 tags
INFO:apps.shared.middleware.request_interceptor:RESPONSE: GET / - 200 (1.84ms)
INFO:     127.0.0.1:51880 - "GET /?lesson=2 HTTP/1.1" 200 OK
INFO:apps.shared.middleware.request_interceptor:REQUEST: GET /.well-known/appspecific/com.chrome.devtools.json
INFO:apps.shared.middleware.request_interceptor:RESPONSE: GET /.well-known/appspecific/com.chrome.devtools.json - 404 (1.20ms)
INFO:     127.0.0.1:51880 - "GET /.well-known/appspecific/com.chrome.devtools.json HTTP/1.1" 404 Not Found
INFO:apps.shared.middleware.request_interceptor:REQUEST: GET /api/user/preferences
INFO:     127.0.0.1:51880 - "GET /api/user/preferences HTTP/1.1" 500 Internal Server Error
ERROR:    Exception in ASGI application
  + Exception Group Traceback (most recent call last):
  |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_utils.py", line 79, in collapse_excgroups
  |     yield
  |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 183, in __call__
  |     async with anyio.create_task_group() as task_group:
  |                ~~~~~~~~~~~~~~~~~~~~~~~^^
  |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/anyio/_backends/_asyncio.py", line 772, in __aexit__
  |     raise BaseExceptionGroup(
  |         "unhandled errors in a TaskGroup", self._exceptions
  |     ) from None
  | ExceptionGroup: unhandled errors in a TaskGroup (1 sub-exception)
  +-+---------------- 1 ----------------
    | Traceback (most recent call last):
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/protocols/http/h11_impl.py", line 403, in run_asgi
    |     result = await app(  # type: ignore[func-returns-value]
    |              ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |         self.scope, self.receive, self.send
    |         ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |     )
    |     ^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    |     return await self.app(scope, receive, send)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/applications.py", line 1054, in __call__
    |     await super().__call__(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/applications.py", line 113, in __call__
    |     await self.middleware_stack(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 186, in __call__
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 164, in __call__
    |     await self.app(scope, receive, _send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 29, in __call__
    |     await responder(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 130, in __call__
    |     await super().__call__(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 46, in __call__
    |     await self.app(scope, receive, self.send_with_compression)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 182, in __call__
    |     with recv_stream, send_stream, collapse_excgroups():
    |                                    ~~~~~~~~~~~~~~~~~~^^
    |   File "/opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/lib/python3.13/contextlib.py", line 162, in __exit__
    |     self.gen.throw(value)
    |     ~~~~~~~~~~~~~~^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_utils.py", line 85, in collapse_excgroups
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 184, in __call__
    |     response = await self.dispatch_func(request, call_next)
    |                ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 60, in dispatch
    |     return await intercept_request(request, call_next)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 42, in intercept_request
    |     response = await call_next(request)
    |                ^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 159, in call_next
    |     raise app_exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 144, in coro
    |     await self.app(scope, receive_or_disconnect, send_no_error)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    |     await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    |     await app(scope, receive, sender)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 716, in __call__
    |     await self.middleware_stack(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 736, in app
    |     await route.handle(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 290, in handle
    |     await self.app(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 78, in app
    |     await wrap_app_handling_exceptions(app, request)(scope, receive, send)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    |     raise exc
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    |     await app(scope, receive, sender)
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 75, in app
    |     response = await f(request)
    |                ^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 302, in app
    |     raw_response = await run_endpoint_function(
    |                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |     ...<3 lines>...
    |     )
    |     ^
    |   File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 213, in run_endpoint_function
    |     return await dependant.call(**values)
    |            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    |   File "/Users/adam/dev/multicardz/apps/user/routes/cards_api.py", line 1084, in get_user_preferences
    |     from apps.shared.config.database import get_db_path
    | ImportError: cannot import name 'get_db_path' from 'apps.shared.config.database' (/Users/adam/dev/multicardz/apps/shared/config/database.py)
    +------------------------------------

During handling of the above exception, another exception occurred:

Traceback (most recent call last):
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/protocols/http/h11_impl.py", line 403, in run_asgi
    result = await app(  # type: ignore[func-returns-value]
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        self.scope, self.receive, self.send
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/uvicorn/middleware/proxy_headers.py", line 60, in __call__
    return await self.app(scope, receive, send)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/applications.py", line 1054, in __call__
    await super().__call__(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/applications.py", line 113, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 186, in __call__
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/errors.py", line 164, in __call__
    await self.app(scope, receive, _send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 29, in __call__
    await responder(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 130, in __call__
    await super().__call__(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/gzip.py", line 46, in __call__
    await self.app(scope, receive, self.send_with_compression)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 182, in __call__
    with recv_stream, send_stream, collapse_excgroups():
                                   ~~~~~~~~~~~~~~~~~~^^
  File "/opt/homebrew/Cellar/python@3.13/3.13.7/Frameworks/Python.framework/Versions/3.13/lib/python3.13/contextlib.py", line 162, in __exit__
    self.gen.throw(value)
    ~~~~~~~~~~~~~~^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_utils.py", line 85, in collapse_excgroups
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 184, in __call__
    response = await self.dispatch_func(request, call_next)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 60, in dispatch
    return await intercept_request(request, call_next)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/apps/shared/middleware/request_interceptor.py", line 42, in intercept_request
    response = await call_next(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 159, in call_next
    raise app_exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/base.py", line 144, in coro
    await self.app(scope, receive_or_disconnect, send_no_error)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/middleware/exceptions.py", line 63, in __call__
    await wrap_app_handling_exceptions(self.app, conn)(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 716, in __call__
    await self.middleware_stack(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 736, in app
    await route.handle(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 290, in handle
    await self.app(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 78, in app
    await wrap_app_handling_exceptions(app, request)(scope, receive, send)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 53, in wrapped_app
    raise exc
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/_exception_handler.py", line 42, in wrapped_app
    await app(scope, receive, sender)
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/starlette/routing.py", line 75, in app
    response = await f(request)
               ^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 302, in app
    raw_response = await run_endpoint_function(
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ...<3 lines>...
    )
    ^
  File "/Users/adam/dev/multicardz/.venv/lib/python3.13/site-packages/fastapi/routing.py", line 213, in run_endpoint_function
    return await dependant.call(**values)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/adam/dev/multicardz/apps/user/routes/cards_api.py", line 1084, in get_user_preferences
    from apps.shared.config.database import get_db_path
ImportError: cannot import name 'get_db_path' from 'apps.shared.config.database' (/Users/adam/dev/multicardz/apps/shared/config/database.py)
INFO:apps.shared.middleware.request_interceptor:REQUEST: GET /api/lessons/options
INFO:apps.shared.middleware.request_interceptor:RESPONSE: GET /api/lessons/options - 200 (0.22ms)
INFO:     127.0.0.1:51881 - "GET /api/lessons/options?completed=%5B%5D HTTP/1.1" 200 OK
INFO:apps.shared.middleware.request_interceptor:REQUEST: POST /api/render/cards
INFO:apps.user.routes.cards_api:Processing 6 zones
INFO:apps.user.routes.cards_api:Using database: /var/data/tutorial_customer.db
INFO:apps.user.routes.cards_api:Loading cards for lesson 1
INFO:apps.user.routes.cards_api:DB READ: card_id=card_union1_only, name=Card with union1 only
INFO:apps.user.routes.cards_api:CARD OBJECT: id=card_union1_only, title=Card with union1 only, tags=frozenset({'union1'})
INFO:apps.user.routes.cards_api:DB READ: card_id=card_union1_intersection1, name=Card with union1 and intersection1
INFO:apps.user.routes.cards_api:CARD OBJECT: id=card_union1_intersection1, title=Card with union1 and intersection1, tags=frozenset({'intersection1', 'union1'})
INFO:apps.user.routes.cards_api:DB READ: card_id=card_union2_only, name=Card with union2 only
INFO:apps.user.routes.cards_api:CARD OBJECT: id=card_union2_only, title=Card with union2 only, tags=frozenset({'union2'})
INFO:apps.user.routes.cards_api:DB READ: card_id=card_union2_column1, name=Card with union2 and column1
INFO:apps.user.routes.cards_api:CARD OBJECT: id=card_union2_column1, title=Card with union2 and column1, tags=frozenset({'union2', 'column1'})
INFO:apps.user.routes.cards_api:DB READ: card_id=card_union2_row1, name=Card with union2 and row1
INFO:apps.user.routes.cards_api:CARD OBJECT: id=card_union2_row1, title=Card with union2 and row1, tags=frozenset({'union2', 'row1'})
INFO:apps.user.routes.cards_api:Loaded 5 cards
INFO:apps.user.routes.cards_api:No operations, showing 0 always_visible cards
INFO:apps.user.routes.cards_api:Rendering dimensional grid: 0 cards, rows=[], cols=[]
INFO:apps.user.routes.cards_api:Converted 0 cards to template format
INFO:apps.user.routes.cards_api:Tag order for color assignment (alphabetical): []
INFO:apps.user.routes.cards_api:Successfully rendered dimensional grid HTML (376 chars)
INFO:apps.user.routes.cards_api:Request completed in 1.77ms
INFO:apps.shared.middleware.request_interceptor:RESPONSE: POST /api/render/cards - 200 (2.12ms)
INFO:     127.0.0.1:51881 - "POST /api/render/cards HTTP/1.1" 200 OK
INFO:apps.shared.middleware.request_interceptor:REQUEST: GET /api/lessons/hint
INFO:apps.shared.middleware.request_interceptor:RESPONSE: GET /api/lessons/hint - 200 (0.23ms)
INFO:     127.0.0.1:51881 - "GET /api/lessons/hint HTTP/1.1" 200 OK
