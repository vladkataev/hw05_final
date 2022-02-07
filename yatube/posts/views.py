from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render, get_object_or_404, redirect
from django.views.decorators.cache import cache_page
from .models import Follow, Group, Post, User
from .forms import CommentForm, PostForm


COUNT_POSTS: int = 10  # число выводимых постов


def get_page_context(queryset, request):
    paginator = Paginator(queryset, COUNT_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return {
        'page_obj': page_obj,
    }


@cache_page(20)
def index(request):
    """Шаблон главной страницы"""
    template = 'posts/index.html'
    context = get_page_context(Post.objects.all(), request)
    return render(request, template, context)


def group_posts(request, slug):
    """Шаблон с группами постов"""
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    context = {
        'group': group,
    }
    context.update(get_page_context(group.posts.all(), request))
    return render(request, template, context)


def profile(request, username):
    """Шаблон профайла пользователя"""
    user = get_object_or_404(User, username=username)
    template = 'posts/profile.html'
    following = user.is_authenticated and user.following.exists()
    context = {
        'author': user,
        'count_posts': user.posts.count(),
        'following': following,
    }
    context.update(get_page_context(user.posts.all(), request))
    return render(request, template, context)


def post_detail(request, post_id):
    """Шаблон страницы поста"""
    post = get_object_or_404(Post, pk=post_id)
    user = post.author
    count_posts = user.posts.all().count()
    form = CommentForm()
    comments = post.comments.all()
    template = 'posts/post_detail.html'
    context = {
        'post': post,
        'author': user,
        'count_posts': count_posts,
        'form': form,
        'comments': comments,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    """Шаблон создания поста"""
    template = 'posts/create_post.html'
    form = PostForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', username=request.user)
    context = {
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    """Шаблон редактирования поста"""
    post = get_object_or_404(Post, pk=post_id)
    template = 'posts/create_post.html'
    if post.author == request.user:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=post
        )
        if request.method == 'POST' and form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:post_detail', post_id=post_id)
        context = {
            'form': form,
            'post': post,
            'is_edit': True,
        }
        return render(request, template, context)
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    posts = Post.objects.filter(author__following__user=request.user)
    template = 'posts/follow.html'
    context = get_page_context(posts.all(), request)
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author:
        Follow.objects.get_or_create(user=request.user, author=author)
    return redirect('posts:profile', author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    unfollowing = Follow.objects.filter(user=request.user, author=author)
    unfollowing.delete()
    return redirect('posts:profile', author)
