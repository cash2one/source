# encoding: utf-8
import datetime

from south.db import db
from south.v2 import SchemaMigration

from django.db import models


class Migration(SchemaMigration):
    depends_on = (
        ("accounts", "0001_initial"),
    )

    def forwards(self, orm):
        # Adding model 'Product'
        db.create_table('products_product', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('deposit_amount', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=2)),
            ('currency', self.gf('django.db.models.fields.CharField')(default='EUR', max_length=3)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('address', self.gf('django.db.models.fields.related.ForeignKey')(related_name='products', to=orm['accounts.Address'])),
            ('quantity', self.gf('django.db.models.fields.IntegerField')()),
            ('is_archived', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('is_allowed', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='products', to=orm['products.Category'])),
            ('owner', self.gf('django.db.models.fields.related.ForeignKey')(related_name='products', to=orm['accounts.Patron'])),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
        ))
        db.send_create_signal('products', ['Product'])

        # Adding model 'Picture'
        db.create_table('products_picture', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='pictures', null=True, to=orm['products.Product'])),
            ('image', self.gf('django.db.models.fields.files.ImageField')(max_length=100, null=True, blank=True)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
        ))
        db.send_create_signal('products', ['Picture'])

        # Adding model 'Category'
        db.create_table('products_category', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='childrens', null=True, to=orm['products.Category'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('slug', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50, db_index=True)),
            ('need_insurance', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('lft', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('rght', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('tree_id', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
            ('level', self.gf('django.db.models.fields.PositiveIntegerField')(db_index=True)),
        ))
        db.send_create_signal('products', ['Category'])

        # Adding model 'Property'
        db.create_table('products_property', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('category', self.gf('django.db.models.fields.related.ForeignKey')(related_name='properties', to=orm['products.Category'])),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255)),
        ))
        db.send_create_signal('products', ['Property'])

        # Adding model 'PropertyValue'
        db.create_table('products_propertyvalue', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('property', self.gf('django.db.models.fields.related.ForeignKey')(related_name='values', to=orm['products.Property'])),
            ('value', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='properties', to=orm['products.Product'])),
        ))
        db.send_create_signal('products', ['PropertyValue'])

        # Adding unique constraint on 'PropertyValue', fields ['property', 'product']
        db.create_unique('products_propertyvalue', ['property_id', 'product_id'])

        # Adding model 'Price'
        db.create_table('products_price', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=2)),
            ('currency', self.gf('django.db.models.fields.CharField')(default='EUR', max_length=3)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='prices', to=orm['products.Product'])),
            ('unit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(db_index=True)),
            ('started_at', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
            ('ended_at', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('products', ['Price'])

        # Adding unique constraint on 'Price', fields ['product', 'unit', 'name']
        db.create_unique('products_price', ['product_id', 'unit', 'name'])

        # Adding model 'ProductReview'
        db.create_table('products_productreview', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('score', self.gf('django.db.models.fields.FloatField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15, null=True, blank=True)),
            ('reviewer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='productreview_reviews', to=orm['accounts.Patron'])),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reviews', to=orm['products.Product'])),
        ))
        db.send_create_signal('products', ['ProductReview'])

        # Adding model 'PatronReview'
        db.create_table('products_patronreview', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('summary', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('score', self.gf('django.db.models.fields.FloatField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')(blank=True)),
            ('ip', self.gf('django.db.models.fields.IPAddressField')(max_length=15, null=True, blank=True)),
            ('reviewer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='patronreview_reviews', to=orm['accounts.Patron'])),
            ('patron', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reviews', to=orm['accounts.Patron'])),
        ))
        db.send_create_signal('products', ['PatronReview'])

        # Adding model 'Question'
        db.create_table('products_question', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('modified_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('status', self.gf('django.db.models.fields.PositiveSmallIntegerField')(default=0, db_index=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='questions', to=orm['products.Product'])),
            ('author', self.gf('django.db.models.fields.related.ForeignKey')(related_name='questions', to=orm['accounts.Patron'])),
        ))
        db.send_create_signal('products', ['Question'])

        # Adding model 'Answer'
        db.create_table('products_answer', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('text', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('created_at', self.gf('django.db.models.fields.DateTimeField')()),
            ('question', self.gf('django.db.models.fields.related.ForeignKey')(related_name='answers', to=orm['products.Question'])),
        ))
        db.send_create_signal('products', ['Answer'])

        # Adding model 'Curiosity'
        db.create_table('products_curiosity', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('product', self.gf('django.db.models.fields.related.ForeignKey')(related_name='curiosities', to=orm['products.Product'])),
        ))
        db.send_create_signal('products', ['Curiosity'])
    
    def backwards(self, orm):
        # Removing unique constraint on 'Price', fields ['product', 'unit', 'name']
        db.delete_unique('products_price', ['product_id', 'unit', 'name'])

        # Removing unique constraint on 'PropertyValue', fields ['property', 'product']
        db.delete_unique('products_propertyvalue', ['property_id', 'product_id'])

        # Deleting model 'Product'
        db.delete_table('products_product')

        # Deleting model 'Picture'
        db.delete_table('products_picture')

        # Deleting model 'Category'
        db.delete_table('products_category')

        # Deleting model 'Property'
        db.delete_table('products_property')

        # Deleting model 'PropertyValue'
        db.delete_table('products_propertyvalue')

        # Deleting model 'Price'
        db.delete_table('products_price')

        # Deleting model 'ProductReview'
        db.delete_table('products_productreview')

        # Deleting model 'PatronReview'
        db.delete_table('products_patronreview')

        # Deleting model 'Question'
        db.delete_table('products_question')

        # Deleting model 'Answer'
        db.delete_table('products_answer')

        # Deleting model 'Curiosity'
        db.delete_table('products_curiosity')
    
    models = {
        'accounts.address': {
            'Meta': {'object_name': 'Address'},
            'address1': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'address2': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'city': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'country': ('django.db.models.fields.CharField', [], {'max_length': '2'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'patron': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'addresses'", 'to': "orm['accounts.Patron']"}),
            'position': ('django.contrib.gis.db.models.fields.PointField', [], {'null': 'True', 'blank': 'True'}),
            'zipcode': ('django.db.models.fields.CharField', [], {'max_length': '9'})
        },
        'accounts.patron': {
            'Meta': {'object_name': 'Patron', '_ormbases': ['auth.User']},
            'activation_key': ('django.db.models.fields.CharField', [], {'max_length': '40', 'null': 'True', 'blank': 'True'}),
            'civility': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'company_name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'is_professional': ('django.db.models.fields.NullBooleanField', [], {'default': 'None', 'null': 'True', 'blank': 'True'}),
            'is_subscribed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {}),
            'paypal_email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'user_ptr': ('django.db.models.fields.related.OneToOneField', [], {'to': "orm['auth.User']", 'unique': 'True', 'primary_key': 'True'})
        },
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'products.answer': {
            'Meta': {'object_name': 'Answer'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'question': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'answers'", 'to': "orm['products.Question']"}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'products.category': {
            'Meta': {'ordering': "['name']", 'object_name': 'Category'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'level': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'lft': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'need_insurance': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'childrens'", 'null': 'True', 'to': "orm['products.Category']"}),
            'rght': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'tree_id': ('django.db.models.fields.PositiveIntegerField', [], {'db_index': 'True'})
        },
        'products.curiosity': {
            'Meta': {'object_name': 'Curiosity'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'curiosities'", 'to': "orm['products.Product']"})
        },
        'products.patronreview': {
            'Meta': {'object_name': 'PatronReview'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'patron': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviews'", 'to': "orm['accounts.Patron']"}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'patronreview_reviews'", 'to': "orm['accounts.Patron']"}),
            'score': ('django.db.models.fields.FloatField', [], {}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'products.picture': {
            'Meta': {'object_name': 'Picture'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'pictures'", 'null': 'True', 'to': "orm['products.Product']"})
        },
        'products.price': {
            'Meta': {'unique_together': "(('product', 'unit', 'name'),)", 'object_name': 'Price'},
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'EUR'", 'max_length': '3'}),
            'ended_at': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'prices'", 'to': "orm['products.Product']"}),
            'started_at': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'unit': ('django.db.models.fields.PositiveSmallIntegerField', [], {'db_index': 'True'})
        },
        'products.product': {
            'Meta': {'object_name': 'Product'},
            'address': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': "orm['accounts.Address']"}),
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': "orm['products.Category']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'currency': ('django.db.models.fields.CharField', [], {'default': "'EUR'", 'max_length': '3'}),
            'deposit_amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_allowed': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'is_archived': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'owner': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'products'", 'to': "orm['accounts.Patron']"}),
            'quantity': ('django.db.models.fields.IntegerField', [], {}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'products.productreview': {
            'Meta': {'object_name': 'ProductReview'},
            'created_at': ('django.db.models.fields.DateTimeField', [], {'blank': 'True'}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ip': ('django.db.models.fields.IPAddressField', [], {'max_length': '15', 'null': 'True', 'blank': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviews'", 'to': "orm['products.Product']"}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'productreview_reviews'", 'to': "orm['accounts.Patron']"}),
            'score': ('django.db.models.fields.FloatField', [], {}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'})
        },
        'products.property': {
            'Meta': {'object_name': 'Property'},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'properties'", 'to': "orm['products.Category']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'products.propertyvalue': {
            'Meta': {'unique_together': "(('property', 'product'),)", 'object_name': 'PropertyValue'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'properties'", 'to': "orm['products.Product']"}),
            'property': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'values'", 'to': "orm['products.Property']"}),
            'value': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'products.question': {
            'Meta': {'ordering': "('modified_at', 'created_at')", 'object_name': 'Question'},
            'author': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'questions'", 'to': "orm['accounts.Patron']"}),
            'created_at': ('django.db.models.fields.DateTimeField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified_at': ('django.db.models.fields.DateTimeField', [], {}),
            'product': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'questions'", 'to': "orm['products.Product']"}),
            'status': ('django.db.models.fields.PositiveSmallIntegerField', [], {'default': '0', 'db_index': 'True'}),
            'text': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        }
    }

    complete_apps = ['products']
