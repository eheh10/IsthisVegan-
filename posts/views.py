from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Post, RatedPost, Comment
import json
from .forms import PostForm, RatedPostForm

# Create your views here.
def post_list(request):
    if request.method == "GET":
        category = request.GET["category"]

        if category == "INFO" or category == "COMMUNICATE":
            posts = Post.objects.filter(category=category)
        else:
            posts = RatedPost.objects.filter(category=category)

        ctx = {
            "posts": posts,
            "category": category,
        }

        if category == "INFO" or category == "COMMUNICATE":
            return render(request, "posts/post_list.html", ctx)
        else:
            return render(request, "posts/rated_post_list.html", ctx)


def post_detail(request, pk):
    if request.method == "GET":
        category = request.GET["category"]
        if category == "INFO" or category == "COMMUNICATE":
            post = get_object_or_404(Post, pk=pk)
        elif category == "VISIT" or category == "BUY":
            post = get_object_or_404(RatedPost, pk=pk)
        comments = post.comments.all()
        bookmarked = request.user.bookmarks.filter(pk=pk).exists()
        ctx = {
            "post": post,
            "category": category,
            "comments": comments,
            "bookmarked": bookmarked,
        }
        if category == "INFO" or category == "COMMUNICATE":
            return render(request, "posts/post_detail.html", ctx)
        elif category == "VISIT" or category == "BUY":
            return render(request, "posts/rated_post_detail.html", ctx)


def on_bookmark_btn_clicked(request):
    data = json.loads(request.body)
    postPk = data["postPk"]
    post = get_object_or_404(Post, pk=postPk)
    bookmarked = request.user.bookmarks.filter(pk=postPk).exists()
    if bookmarked:
        request.user.bookmarks.remove(post)
        bookmarked = False
    else:
        request.user.bookmarks.add(post)
        bookmarked = True
    return JsonResponse(bookmarked, safe=False)


def on_post_like_btn_clicked(request):
    data = json.loads(request.body)
    postPk = data["postPk"]
    post = get_object_or_404(Post, pk=postPk)
    liked = post.like.filter(pk=request.user.pk).exists()
    if liked:
        post.like.remove(request.user)
        liked = False
    else:
        post.like.add(request.user)
        liked = True
    likedTotal = len(post.like.all())
    ctx = {"liked": liked, "likedTotal": likedTotal}
    return JsonResponse(ctx)


def on_comment_like_btn_clicked(request):
    data = json.loads(request.body)
    commentPk = data["commentPk"]
    comment = get_object_or_404(Comment, pk=commentPk)
    liked = comment.like.filter(pk=request.user.pk).exists()
    if liked:
        comment.like.remove(request.user)
        liked = False
    else:
        comment.like.add(request.user)
        liked = True
    likedTotal = len(comment.like.all())
    ctx = {"liked": liked, "likedTotal": likedTotal}
    return JsonResponse(ctx)


def comment_create(request):
    data = json.loads(request.body)
    postPk = data["postPk"]
    content = data["content"]
    category = data["category"]

    if category == "INFO" or category == "COMMUNICATE":
        post = get_object_or_404(Post, pk=postPk)
    elif category == "VISIT" or category == "BUY":
        post = get_object_or_404(RatedPost, pk=postPk)

    newComment = Comment(
        post=post, object_id=postPk, content=content, user=request.user
    )
    newComment.save()

    comments = post.comments.all()
    # comments = list(comments.values())
    commentList = []
    for comment in comments:
        aComment = {
            "id": comment.id,
            "nickname": comment.user.nickname,
            "user_id": comment.user.id,
            "content": comment.content,
            "written_by_user": comment.user == request.user,
            "liked": comment.like.filter(pk=request.user.pk).exists(),
            "liked_total": len(comment.like.all()),
        }
        commentList.append(aComment)

    return JsonResponse(commentList, safe=False)


def comment_delete(request):
    data = json.loads(request.body)
    commentPk = data["commentPk"]

    comment = get_object_or_404(Comment, pk=commentPk)
    # 요청자가 댓글 작성자가 아닌 경우 False return
    if comment.user != request.user:
        return JsonResponse(False, safe=False)

    post = comment.post

    comment.delete()

    comments = post.comments.all()
    # comments = list(comments.values())
    commentList = []
    for comment in comments:
        aComment = {
            "id": comment.id,
            "nickname": comment.user.nickname,
            "user_id": comment.user.id,
            "content": comment.content,
            "written_by_user": comment.user == request.user,
            "liked": comment.like.filter(pk=request.user.pk).exists(),
            "liked_total": len(comment.like.all()),
        }
        commentList.append(aComment)

    return JsonResponse(commentList, safe=False)


def post_create(request):
    category = request.GET["category"]

    if request.method == "GET":
        if category in ["INFO", "COMMUNICATE"]:
            form = PostForm()
        else:
            form = RatedPostForm()

        ctx = {
            "form": form,
            "category": category,
        }
        return render(request, "posts/post_create.html", ctx)
    else:
        pk = 0
        if category in ["INFO", "COMMUNICATE"]:
            form = PostForm(request.POST)

            if form.is_valid():
                post = form.save(commit=False)
                post.user = request.user
                post.category = category
                post.save()
                pk = post.id
        else:
            form = RatedPostForm(request.POST)

            if form.is_valid():
                ratedpost = form.save(commit=False)
                ratedpost.user = request.user
                ratedpost.category = category
                ratedpost.save()
                pk = ratedpost.id

        return redirect(f"/detail/{pk}?category={category}")


def post_update(request, pk):
    category = request.GET["category"]

    if request.method == "GET":
        if category in ["INFO", "COMMUNICATE"]:
            post = get_object_or_404(Post, id=pk)
            form = PostForm(instance=post)
        else:
            post = get_object_or_404(RatedPost, id=pk)
            form = RatedPostForm(instance=post)

        ctx = {
            "form": form,
            "category": category,
        }
        return render(request, "posts/post_create.html", ctx)
    else:
        if category in ["INFO", "COMMUNICATE"]:
            post = get_object_or_404(Post, id=pk)
            form = PostForm(request.POST, request.FILES, instance=post)
        else:
            post = get_object_or_404(RatedPost, id=pk)
            form = RatedPostForm(request.POST, request.FILES, instance=post)

        if form.is_valid():
            post.save()
        return redirect(f"/detail/{pk}?category={category}")


def post_delete(request, pk):
    category = request.GET["category"]

    if category in ["INFO", "COMMUNICATE"]:
        post = get_object_or_404(Post, id=pk)
    else:
        post = get_object_or_404(RatedPost, id=pk)

    post.delete()
    return redirect(f"/posts/?category={category}")


def main(request):
    posts = Post.objects.all()
    # 유진아 마이페이지 잘 연결되는지 확인하려고 내가 pk 추가했어!! 놀라지말길
    pk = request.user.id
    ctx = {"posts": posts, "pk": pk}
    return render(request, "posts/main.html", ctx)
