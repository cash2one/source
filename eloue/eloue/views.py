from django import http
from django.views.decorators.csrf import requires_csrf_token
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.generic import View
from django.template import Context, RequestContext, loader

from products.forms import FacetedSearchForm

@requires_csrf_token
def custom404(request, template_name='404.html'):
    """
    Default 404 handler.

    Templates: `404.html`
    Context:
        request_path
            The path of the requested URL (e.g., '/app/pages/bad_page/')
    """
    t = loader.get_template(template_name) # You need to create a 404.html template.
    form = FacetedSearchForm()
    return http.HttpResponseNotFound(
    	t.render(RequestContext(request, {'request_path': request.path, 'form': form}))
    )

class LoginRequiredMixin(View):
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super(LoginRequiredMixin, self).dispatch(*args, **kwargs)