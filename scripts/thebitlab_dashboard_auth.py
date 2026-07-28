"""Provider-independent role and class authorization for web dashboards."""

from __future__ import annotations

from scripts.thebitlab_dashboard_auth_ports import (
    DashboardAccessScope,
    DashboardAuthorizationSnapshot,
    DashboardAuthorizationStorage,
    dashboard_identifier,
)
from scripts.thebitlab_http_auth import (
    HttpAuthContext,
    HttpAuthError,
    HttpAuthRequest,
    HttpAuthorizationDeniedError,
    HttpSessionAuthBoundary,
)


class DashboardAuthorizationUnavailableError(HttpAuthError):
    """Stable infrastructure error suitable for an HTTP 503 response."""

    status_code = 503
    error_code = "dashboard_authorization_unavailable"
    public_message = "Autorizzazione dashboard temporaneamente non disponibile."

    def __init__(self) -> None:
        super().__init__()


class DashboardAuthorizationBoundary:
    """Combine live HTTP sessions with role and class-scoped dashboard policies."""

    def __init__(
        self,
        http_sessions: HttpSessionAuthBoundary,
        storage: DashboardAuthorizationStorage,
    ) -> None:
        self.http_sessions = http_sessions
        self.storage = storage

    def authorize_teacher_dashboard(
        self, request: HttpAuthRequest
    ) -> DashboardAccessScope:
        context = self.http_sessions.authorize_application(
            request, allowed_roles={"admin", "teacher"}
        )
        snapshot = self._snapshot(context)
        if snapshot.actor_role == "admin":
            return DashboardAccessScope(
                "teacher", snapshot.actor_user_id, (), all_classes=True
            )
        if snapshot.actor_role != "teacher" or not snapshot.actor_class_ids:
            raise HttpAuthorizationDeniedError()
        return DashboardAccessScope(
            "teacher", snapshot.actor_user_id, snapshot.actor_class_ids
        )

    def authorize_student_dashboard(
        self,
        request: HttpAuthRequest,
        *,
        requested_student_user_id: str,
    ) -> DashboardAccessScope:
        context = self.http_sessions.authorize_application(
            request, allowed_roles={"admin", "teacher", "student"}
        )
        try:
            target_user_id = dashboard_identifier(
                requested_student_user_id, "requested_student_user_id"
            )
        except ValueError:
            raise HttpAuthorizationDeniedError() from None
        if context.user.role == "student" and target_user_id != context.user.user_id:
            raise HttpAuthorizationDeniedError()
        snapshot = self._snapshot(context, target_user_id=target_user_id)
        if (
            snapshot.target_user_id != target_user_id
            or snapshot.target_role != "student"
            or not snapshot.target_class_ids
        ):
            raise HttpAuthorizationDeniedError()
        if snapshot.actor_role == "admin":
            visible = snapshot.target_class_ids
        elif snapshot.actor_role == "student":
            if snapshot.actor_user_id != target_user_id:
                raise HttpAuthorizationDeniedError()
            visible = tuple(
                sorted(set(snapshot.actor_class_ids) & set(snapshot.target_class_ids))
            )
        elif snapshot.actor_role == "teacher":
            visible = tuple(
                sorted(set(snapshot.actor_class_ids) & set(snapshot.target_class_ids))
            )
        else:
            raise HttpAuthorizationDeniedError()
        if not visible:
            raise HttpAuthorizationDeniedError()
        return DashboardAccessScope(
            "student",
            snapshot.actor_user_id,
            visible,
            student_user_id=target_user_id,
        )

    def _snapshot(
        self, context: HttpAuthContext, *, target_user_id: str | None = None
    ) -> DashboardAuthorizationSnapshot:
        snapshot = None
        unavailable = False
        try:
            snapshot = self.storage.read_dashboard_authorization_snapshot(
                context.user.user_id,
                expected_actor_updated_at=context.user.updated_at,
                target_user_id=target_user_id,
            )
        except Exception:
            unavailable = True
        if unavailable:
            raise DashboardAuthorizationUnavailableError()
        if snapshot is None:
            raise HttpAuthorizationDeniedError()
        if type(snapshot) is not DashboardAuthorizationSnapshot:
            raise DashboardAuthorizationUnavailableError()
        if (
            snapshot.actor_user_id != context.user.user_id
            or snapshot.actor_role != context.user.role
            or snapshot.actor_updated_at != context.user.updated_at
        ):
            raise DashboardAuthorizationUnavailableError()
        return snapshot
