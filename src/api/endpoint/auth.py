import base64
from dataclasses import dataclass
import httpx
from sanic import Blueprint, Request, HTTPResponse, response
from sanic_ext import validate
import jwt
import binascii
import time
import uuid
from typing import Optional
import aiofiles
import urllib.parse

from ..auth import auth_response, AuthResponse, AuthError, oauth2_redirect, oauth2_check_state, del_cookie
from ...state import User
from ...logic import Worker
from ... import secret
from ..mailsend import check_ip, gen_email_link, decode_mail_link, check_mail

# try:
#     from .auth_pku import iaaa_login, iaaa_check
# except ImportError:
#     print('WARNING: pku auth not implemented')
#     async def iaaa_login() -> HTTPResponse:
#         return response.text('not implemented')
#     async def iaaa_check(req: Request, http_client: httpx.AsyncClient, worker: Worker) -> AuthResponse:
#         raise AuthError('not implemented')

bp = Blueprint('auth', url_prefix='/auth')

@bp.route("/mail/send", methods=["POST"])
async def auth_uestc_mail_send(_req: Request) -> HTTPResponse:
    """
    邮寄验证邮件的接口
    :param _req:
    :return:返回一个json，包含两个部分，一个是success，一个是message
    """
    message = check_ip(_req.headers["X-Forwarded-For"].split(",")[0])
    if not (message.__eq__("IP地址认证成功") or message.__eq__("IP地址在白名单中")):
        return response.json(
            {
                "success": False,
                "message": message,
            }
        )
    _req_json = _req.json
    email = _req_json["email"]

    message = check_mail(email)
    if not (message.__eq__("邮箱认证成功") or message.__eq__("邮箱在白名单中")):
        return response.json(
            {
                "success": False,
                "message": message,
            }
        )

    auth_root = _req_json["auth_root"]
    url = _req_json["url"]
    if not auth_root or not url:
        return response.json(
            {
                "success": False,
                "message": "参数不正确",
            }
        )

    async with aiofiles.open("statics/email/MailTemplate.html", "rb") as f:
        html = await f.read()
        html = html.decode("utf-8")

    url_parse = urllib.parse.urlparse(url)
    url = f"{url_parse.scheme}://{url_parse.netloc}{auth_root}mail/check?auth={gen_email_link(email)}"
    content = html.replace("{{url}}", url)

    # 从req的post中获取email
    await _req.app.ctx.smtp_connect(_req.app, None)
    await _req.app.ctx.send_email(

        targetlist=email,
        subject="【御林安全】平台授权登陆",
        content=content,
        html=True,
        sendername="YulinSec",
    )
    await _req.app.ctx.smtp_close(_req.app, None)

    _req.app.ctx.worker.log(
        "info",
        "login.auth",
        "IP: {},email: {}".format(_req.headers["X-Forwarded-For"], email),
    )

    return response.json(
        {
            "success": True,
            "message": "请在邮箱中查收邮件！",
        }
    )

@bp.route("/mail/check", methods=["GET"])
@auth_response
async def auth_uestc_res(_req: Request) -> AuthResponse:
    auth_dict = decode_mail_link(_req.args.get("auth"))

    if auth_dict.get("time_sec") < 15:
        return (
            f"{auth_dict.get('user_group')}:{auth_dict.get('email')}",
            {
                "type": auth_dict.get("user_group"),
                "info": {"email": f"{auth_dict.get('email')}"},
            },
            auth_dict.get("user_group"),
        )
    else:
        raise AuthError("链接已过期")

@bp.route('/logout')
async def auth_logout(_req: Request, user: Optional[User]) -> HTTPResponse:
    res = response.redirect(secret.FRONTEND_PORTAL_URL)
    del_cookie(res, 'auth_token')
    if user and secret.IS_ADMIN(user._store):
        del_cookie(res, 'admin_2fa', secret.ADMIN_URL)
    return res

if secret.MANUAL_AUTH_ENABLED:
    @dataclass
    class AuthManualParam:
        identity: str

    @bp.route('/manual')
    @validate(query=AuthManualParam)
    @auth_response
    async def auth_manual(_req: Request, query: AuthManualParam, _worker: Worker) -> AuthResponse:
        if not secret.MANUAL_AUTH_ENABLED: # impossible, but add a fail safe here
            raise AuthError('手动登录已禁用')

        return f'manual:{query.identity}', {'type': 'manual'}, 'staff'

@dataclass
class AuthSuParam:
    uid: int

@bp.route('/su')
@validate(query=AuthSuParam)
@auth_response
async def auth_su(_req: Request, query: AuthSuParam, worker: Worker, user: Optional[User]) -> AuthResponse:
    if user is None or not secret.IS_ADMIN(user._store):
        raise AuthError('没有权限')
    if worker.game is None:
        raise AuthError('服务暂时不可用')

    su_user = worker.game.users.user_by_id.get(query.uid, None)
    if su_user is None:
        raise AuthError('用户不存在')
    if secret.IS_ADMIN(su_user._store):
        raise AuthError('不能切换到管理员账号')

    return su_user

# if secret.GITHUB_APP_ID:
#     @bp.route('/github/login')
#     async def auth_github_req(req: Request) -> HTTPResponse:
#         assert secret.GITHUB_APP_ID

#         return oauth2_redirect(
#             'https://github.com/login/oauth/authorize',
#             {
#                 'client_id': secret.GITHUB_APP_ID,
#             },
#             secret.BUILD_OAUTH_CALLBACK_URL(
#                 req.app.url_for('auth.auth_github_res', _external=True, _scheme=secret.BACKEND_SCHEME, _server=secret.BACKEND_HOSTNAME)
#             ),
#         )

#     @bp.route('/github/login/callback')
#     @auth_response
#     async def auth_github_res(req: Request, http_client: httpx.AsyncClient, worker: Worker) -> AuthResponse:
#         oauth_code = req.args.get('code', None)
#         if not oauth_code:
#             raise AuthError('OAuth登录失败')

#         oauth2_check_state(req)

#         token_res = await http_client.post('https://github.com/login/oauth/access_token', params={
#             'client_id': secret.GITHUB_APP_ID,
#             'client_secret': secret.GITHUB_APP_SECRET,
#             'code': oauth_code,
#         }, headers={
#             'Accept': 'application/json',
#         })
#         token = token_res.json().get('access_token', None)
#         if token is None:
#             worker.log('warning', 'api.auth.github', f'get access_token failed:\n{token_res.json()}')
#             raise AuthError('GitHub Token不存在')

#         info_res = await http_client.get('https://api.github.com/user', headers={
#             'Authorization': f'token {token}',
#             'Accept': 'application/vnd.github.v3+json',
#         })
#         info = info_res.json()

#         uid = info.get('id', None)
#         if uid is None:
#             worker.log('warning', 'api.auth.github', f'get user failed:\n{info}')
#             raise AuthError('GitHub UID不存在')

#         return f'github:{uid}', {
#             'type': 'github',
#             'info': info,
#             'access_token': token
#         }, 'other'

# if secret.MS_APP_ID:
#     @bp.route('/microsoft/login')
#     async def auth_ms_req(req: Request) -> HTTPResponse:
#         assert secret.MS_APP_ID

#         return oauth2_redirect(
#             'https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize',
#             {
#                 'client_id': secret.MS_APP_ID,
#                 'response_type': 'code',
#                 'response_mode': 'query',
#                 'scope': 'User.Read',
#             },
#             secret.BUILD_OAUTH_CALLBACK_URL(
#                 req.app.url_for('auth.auth_ms_res', _external=True, _scheme=secret.BACKEND_SCHEME, _server=secret.BACKEND_HOSTNAME)
#             ),
#         )

#     @bp.route('/microsoft/login/callback')
#     @auth_response
#     async def auth_ms_res(req: Request, http_client: httpx.AsyncClient, worker: Worker) -> AuthResponse:
#         oauth_code = req.args.get('code', None)
#         if not oauth_code:
#             raise AuthError('OAuth登录失败')

#         oauth2_check_state(req)

#         ts = int(time.time())
#         x5t = base64.urlsafe_b64encode(binascii.unhexlify(secret.MS_PUB_KEY_THUMBPRINT)).decode()

#         assert secret.MS_PRIV_KEY is not None
#         auth_jwt = jwt.encode(
#             payload={
#                 'jti': str(uuid.uuid4()),
#                 'aud': 'https://login.microsoftonline.com/consumers/oauth2/v2.0/token',
#                 'iss': secret.MS_APP_ID,
#                 'sub': secret.MS_APP_ID,
#                 'iat': ts,
#                 'nbf': ts-120,
#                 'exp': ts+480,
#             },
#             key=secret.MS_PRIV_KEY,
#             algorithm='RS256',
#             headers={
#                 'x5t': x5t,
#             },
#         )

#         token_res = await http_client.post('https://login.microsoftonline.com/consumers/oauth2/v2.0/token', data={
#             'client_id': secret.MS_APP_ID,
#             'client_assertion_type': 'urn:ietf:params:oauth:client-assertion-type:jwt-bearer',
#             'client_assertion': auth_jwt,
#             'code': oauth_code,
#             'grant_type': 'authorization_code',
#             'scope': 'User.Read',
#             'redirect_uri': secret.BUILD_OAUTH_CALLBACK_URL(
#                 req.app.url_for('auth.auth_ms_res', _external=True, _scheme=secret.BACKEND_SCHEME, _server=secret.BACKEND_HOSTNAME)
#             ),
#         })
#         token_json = token_res.json()
#         token = token_json.get('access_token', None)
#         if token is None:
#             worker.log('warning', 'api.auth.ms', f'get access_token failed:\n{token_json}')
#             raise AuthError('MS Token不存在')

#         info_res = await http_client.get('https://graph.microsoft.com/v1.0/me', headers={
#             'Authorization': f'Bearer {token}',
#         })
#         info = info_res.json()

#         uid = info.get('id', None)
#         if uid is None:
#             worker.log('warning', 'api.auth.ms', f'get user failed:\n{info}')
#             raise AuthError('MS UID不存在')

#         return f'ms:{uid}', {
#             'type': 'microsoft',
#             'info': info,
#             'access_token': token,
#         }, 'other'

# if secret.IAAA_APP_ID:
#     @bp.route('/pku/redirect')
#     async def auth_pku_req(_req: Request) -> HTTPResponse:
#         return await iaaa_login()

#     @bp.route('/pku/login')
#     @auth_response
#     async def auth_pku_res(req: Request, http_client: httpx.AsyncClient, worker: Worker) -> AuthResponse:
#         return await iaaa_check(req, http_client, worker)

# if secret.CARSI_APP_ID:
#     def carsi_decrypt(data_b64: str) -> str:
#         assert hasattr(secret, 'CARSI_PRIV_KEY')

#         from cryptography.hazmat.primitives.asymmetric import padding
#         from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey

#         data = base64.b64decode(data_b64.encode())

#         assert secret.CARSI_PRIV_KEY is not None
#         k = secret.CARSI_PRIV_KEY.to_cryptography_key()
#         assert isinstance(k, RSAPrivateKey)

#         return k.decrypt(data, padding.PKCS1v15()).decode()

#     @bp.route('/carsi/login')
#     async def auth_carsi_req(req: Request) -> HTTPResponse:
#         assert secret.CARSI_APP_ID

#         return oauth2_redirect(
#             'https://spoauth2pre.carsi.edu.cn/api/authorize',
#             {
#                 'response_type': 'code',
#                 'client_id': secret.CARSI_APP_ID,
#             },
#             secret.BUILD_OAUTH_CALLBACK_URL(
#                 req.app.url_for('auth.auth_carsi_res', _external=True, _scheme=secret.BACKEND_SCHEME, _server=secret.BACKEND_HOSTNAME)
#             ),
#         )

#     @bp.route('/carsi/login/callback')
#     @auth_response
#     async def auth_carsi_res(req: Request, http_client: httpx.AsyncClient, worker: Worker) -> AuthResponse:
#         oauth_code = req.args.get('code', None)
#         if not oauth_code:
#             raise AuthError('OAuth登录失败')

#         #oauth2_check_state(req)

#         token_res = await http_client.post(f'https://{secret.CARSI_DOMAIN}/api/token', data={
#             'grant_type': 'authorization_code',
#             'client_id': secret.CARSI_APP_ID,
#             'client_secret': secret.CARSI_APP_SECRET,
#             'code': oauth_code,
#         })
#         token = token_res.json().get('access_token', None)
#         if token is None:
#             worker.log('warning', 'api.auth.carsi', f'get access_token failed:\n{token_res.json()}')
#             raise AuthError('Carsi Token不存在')

#         info_res = await http_client.get(f'https://{secret.CARSI_DOMAIN}/api/resource', params={
#             'access_token': token,
#             'client_id': secret.CARSI_APP_ID,
#         })
#         info = info_res.json()

#         uid_enc = info.get('carsi-persistent-uid', None)
#         if uid_enc is None:
#             worker.log('warning', 'api.auth.carsi', f'get user failed:\n{info}')
#             raise AuthError('Carsi UID不存在')

#         uid = carsi_decrypt(uid_enc)
#         affiliation = carsi_decrypt(info['carsi-affiliation'])
#         usertype, _at, domain = affiliation.rpartition('@')
#         assert _at == '@', affiliation

#         return f'carsi:{uid}', {
#             'type': 'carsi',
#             'info': {
#                 'usertype': usertype,
#                 'domain': domain,
#             },
#             'access_token': token
#         }, 'other'

#     @bp.route('/carsi/logout')
#     async def auth_carsi_logout(_req: Request, user: Optional[User]) -> HTTPResponse:
#         res = response.json({"status": 1, "msg": ""})
#         del_cookie(res, 'auth_token')
#         if user and secret.IS_ADMIN(user._store):
#             del_cookie(res, 'admin_2fa', secret.ADMIN_URL)
#         return res