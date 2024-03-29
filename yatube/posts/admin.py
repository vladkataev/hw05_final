from django.contrib import admin
from .models import Comment, Group, Post


class PostAdmin(admin.ModelAdmin):
    list_display = (
        'pk',
        'text',
        'pub_date',
        'author',
        'group'
    )
    list_editable = ('group',)
    search_fields = ('text',)
    list_filter = ('pub_date',)
    empty_value_display = '-пусто-'


class GroupAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'title',
        'slug',
        'description'
    )
    search_fields = (
        'title',
        'description',
        'slug'
    )
    list_filter = ('title',)


class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'post',
        'text',
        'created',
        'author'
    )
    search_fields = ('text',)
    list_filter = (
        'created',
        'author'
    )


admin.site.register(Post, PostAdmin)
admin.site.register(Group, GroupAdmin)
admin.site.register(Comment, CommentAdmin)
